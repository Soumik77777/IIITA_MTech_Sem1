"""
ATR multi-agent debate pipeline.
Agents are independent prompt-defined roles but API requests are sequential.
The debate runs iteratively; each round sees earlier arguments and decisions.
"""

from pathlib import Path
import base64
import json
import time
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

PAUSE_SEC = 10
MAX_RETRIES = 3
DEBATE_ROUNDS = 3
PERSPECTIVES = ("theoretical", "computational", "observational", "experimental")
MAX_CONTEXT_CHARS = 26000
_last_request_completed_at = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _response_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("text") is not None:
                parts.append(str(block["text"]))
            elif isinstance(block, str):
                parts.append(block)
            elif getattr(block, "text", None) is not None:
                parts.append(str(block.text))
        return "\n".join(parts).strip()
    return str(content).strip()


def _usage(response):
    data = getattr(response, "usage_metadata", None) or {}
    inp, out, total = data.get("input_tokens"), data.get("output_tokens"), data.get("total_tokens")
    if total is None and inp is not None and out is not None:
        total = inp + out
    return inp, out, total


def _web_sources(response):
    metadata = getattr(response, "response_metadata", None) or {}
    found = []

    def walk(value):
        if isinstance(value, dict):
            url = value.get("uri") or value.get("url")
            title = value.get("title") or value.get("source_title")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                item = {"title": title or url, "url": url}
                if item not in found:
                    found.append(item)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(metadata.get("groundingMetadata", {}))
    walk(metadata.get("grounding_metadata", {}))
    return found


def _wait():
    global _last_request_completed_at
    if _last_request_completed_at is None:
        return
    remaining = PAUSE_SEC - (time.monotonic() - _last_request_completed_at)
    if remaining > 0:
        print(f"[RATE LIMIT] Waiting {remaining:.1f}s before next request.")
        time.sleep(remaining)


def _retryable(exc):
    message = str(exc).lower()
    return any(x in message for x in (
        "429", "resource_exhausted", "rate limit", "too many requests",
        "503", "service unavailable", "502", "504",
    ))


def _json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                result = json.loads(text[start:end + 1])
                return result if isinstance(result, dict) else None
            except json.JSONDecodeError:
                pass
    return None


def _compact(value, limit=MAX_CONTEXT_CHARS):
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return text if len(text) <= limit else text[:limit] + "\\n[Context truncated.]"


def _call(llm, prompt, *, stage, agent, model_name, prices, history, usage_log,
          paper=None, round_no=None, use_search=False, search_llm=None):
    global _last_request_completed_at
    event = {
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": stage, "agent": agent, "round": round_no,
        "paper": str(Path(paper).resolve()) if paper else None,
        "prompt": prompt, "status": "started",
    }
    history.append(event)
    try:
        if paper:
            encoded = base64.b64encode(Path(paper).read_bytes()).decode("ascii")
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "media", "mime_type": "application/pdf", "data": encoded},
            ])
        else:
            message = HumanMessage(content=prompt)
    except Exception as exc:
        event.update(status="error", error=f"{type(exc).__name__}: {exc}")
        print(f"[ERROR] Could not prepare {paper}: {exc}")
        return None

    selected = search_llm if use_search and search_llm is not None else llm
    if use_search and search_llm is None:
        event["search_warning"] = "Google Search grounding unavailable; request ran without it."

    for attempt in range(1, MAX_RETRIES + 1):
        _wait()
        start = time.perf_counter()
        try:
            response = selected.invoke([message])
            runtime = round(time.perf_counter() - start, 3)
            _last_request_completed_at = time.monotonic()
            inp, out, total = _usage(response)
            cost = None
            if inp is not None and out is not None and prices.get("input") is not None and prices.get("output") is not None:
                cost = (inp * prices["input"] + out * prices["output"]) / 1_000_000
            usage_log.append({
                "timestamp_utc": _now(), "stage": stage, "agent": agent,
                "round": round_no, "paper": event["paper"], "model": model_name,
                "attempt": attempt, "status": "success", "runtime_seconds": runtime,
                "input_tokens": inp, "output_tokens": out, "total_tokens": total,
                "estimated_cost_usd": cost, "error": None,
            })
            text = _response_text(response.content)
            sources = _web_sources(response) if use_search else []
            event.update(status="success", response=text, runtime_seconds=runtime,
                         attempts=attempt, web_sources=sources)
            return text, sources
        except Exception as exc:
            runtime = round(time.perf_counter() - start, 3)
            _last_request_completed_at = time.monotonic()
            error = f"{type(exc).__name__}: {exc}"
            usage_log.append({
                "timestamp_utc": _now(), "stage": stage, "agent": agent,
                "round": round_no, "paper": event["paper"], "model": model_name,
                "attempt": attempt, "status": "error", "runtime_seconds": runtime,
                "input_tokens": None, "output_tokens": None, "total_tokens": None,
                "estimated_cost_usd": None, "error": error,
            })
            if _retryable(exc) and attempt < MAX_RETRIES:
                delay = PAUSE_SEC * (2 ** (attempt - 1))
                print(f"[RETRY] {agent}: attempt {attempt}/{MAX_RETRIES}; waiting {delay}s.")
                time.sleep(delay)
                continue
            event.update(status="error", error=error, runtime_seconds=runtime, attempts=attempt)
            print(f"[ERROR] {agent}: {error}")
            return None
    return None


def _parsed_event(history, raw):
    parsed = _json(raw)
    event = history[-1]
    event["parsed_output"] = parsed
    if parsed is None:
        event["parse_warning"] = "Response was not valid JSON; raw response retained."
    return parsed


def _reader_prompt(topic, additional, paper):
    return f"""
ROLE: Independent Literature Analyst
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
PAPER: {Path(paper).name}

Read only the attached paper. Separate explicit statements from your inference.
For every finding or possible gap, cite this paper and page/section where possible.
Do not assume every limitation is a research gap.

Return ONLY JSON:
{{
 "paper_title":"","authors_year":"","research_question":"","context":"",
 "methods":[],"main_findings":[],"assumptions":[],
 "limitations_explicit":[],
 "potential_open_questions":[{{"question":"","why_unresolved":"","evidence":"","page_or_section":""}}],
 "candidate_hypotheses":[{{"hypothesis":"","rationale":"","evidence":"","page_or_section":""}}]
}}
Do not claim novelty beyond this paper.
"""


def _perspective_prompt(topic, additional, perspective, papers):
    guidance = {
        "theoretical": "Find missing physical explanations, theoretical assumptions, mathematical inconsistencies and untested predictions.",
        "computational": "Find limitations in numerical methods, algorithms, simulations, scalability, reproducibility and computational models.",
        "observational": "Find missing measurements, data limitations, parameter degeneracies and mismatches between models and observations.",
        "experimental": "Find testability gaps and controlled tests, including laboratory, physical, numerical or code-based experiments.",
    }[perspective]
    return f"""
ROLE: Independent {perspective.title()} Research-Gap Analyst
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
PERSPECTIVE: {guidance}

Work independently; do not imitate other perspectives or force agreement.
A limitation is not automatically a gap. Distinguish explicit open problems
from inferred gaps. State what is known, what remains unknown, why it matters,
and exact supporting paper filenames plus evidence/page/section. Do not claim
field-wide novelty; external literature verification follows.

Return ONLY JSON:
{{"perspective":"{perspective}","research_gaps":[
 {{"gap":"","why_it_matters":"","what_is_known":"","what_remains_unknown":"",
   "supporting_papers":[],"evidence":[],"gap_type":"explicit|inferred",
   "confidence":"low|medium|high"}}
]}}

PAPER ANALYSES:
{_compact(papers)}
"""


def _verify_prompt(topic, candidates, kind):
    return f"""
ROLE: External Literature Verification Agent
TOPIC: {topic}
SUBJECT: {kind}

Use Google Search grounding. Search scholarly literature and reliable sources,
prioritizing peer-reviewed papers, arXiv and conference papers. For each
candidate, find the closest prior work, not merely papers mentioning the topic.
Decide whether it is already well studied, partially addressed, contradicted,
possibly open, or unclear. Explain what prior work did and what remains
different. Include source title, authors/year and exact URL. Never invent
citations; state when evidence is weak.

Return ONLY JSON:
{{"verification":[
 {{"target_id":"","status":"well_studied|partially_addressed|contradicted|possibly_open|unclear",
   "closest_prior_work":[{{"title":"","authors_year":"","what_it_did":"","url":""}}],
   "what_remains_unresolved":"","reasoning":"","confidence":"low|medium|high"}}
],"overall_notes":""}}

CANDIDATES:
{_compact(candidates)}
"""


def _assign_ids(items, prefix, perspective):
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if not (item.get("gap") or item.get("hypothesis")):
            continue
        record = dict(item)
        record.update(id=f"{prefix}{len(result)+1:03d}", origin_agent=perspective,
                      status="candidate")
        record.setdefault("supporting_papers", [])
        record.setdefault("evidence", [])
        record.setdefault("debate_history", [])
        result.append(record)
    return result


def _apply_verification(candidates, verification, sources):
    mapping = {
        x.get("target_id"): x for x in verification.get("verification", [])
        if isinstance(x, dict)
    }
    for item in candidates:
        match = mapping.get(item["id"])
        if match:
            item["external_verification"] = match
            item["external_sources"] = match.get("closest_prior_work", [])
            item["external_status"] = match.get("status", "unclear")
            item["external_search_sources"] = sources
    return candidates


def _debate_prompt(topic, kind, perspective, round_no, candidates, prior, verification):
    guidance = {
        "theoretical": "challenge physical logic, assumptions, mechanisms and predictions",
        "computational": "challenge numerical validity, computational feasibility and reproducibility",
        "observational": "challenge empirical support, measurability and observational relevance",
        "experimental": "challenge testability, experimental design, controls and falsifiability",
    }[perspective]
    return f"""
ROLE: {perspective.title()} Debate Agent
TOPIC: {topic}
SUBJECT: {kind}
ROUND: {round_no}/{DEBATE_ROUNDS}
Your responsibility: {guidance}.

This is a debate, not a summary. Review candidates and earlier arguments.
You may challenge, defend, revise, combine compatible candidates, reject, or
propose an alternative. Do not agree merely to reach consensus. Each action
must identify target_id and cite paper filenames/IDs or external URLs.
Mark unsupported reasoning as inference, not fact.

Return ONLY JSON:
{{
 "agent":"{perspective}","round":{round_no},
 "actions":[
  {{"target_id":"","action":"challenge|defend|revise|combine|reject|support|new_candidate",
    "argument":"","evidence":[],"paper_references":[],"external_references":[],
    "proposed_revision":"","combine_with":[],"new_candidate":""}}
 ],
 "cross_candidate_observations":[]
}}

CURRENT CANDIDATES:
{_compact(candidates)}

EXTERNAL VERIFICATION:
{_compact(verification)}

ARGUMENTS FROM EARLIER ROUNDS:
{_compact(prior)}
"""


def _adjudicator_prompt(topic, kind, round_no, candidates, actions):
    return f"""
ROLE: Debate Adjudicator
TOPIC: {topic}
SUBJECT: {kind}
ROUND: {round_no}

Evaluate arguments from all four perspectives. Decide each candidate:
retain, revise, combine, reject, or hold. "Hold" preserves unresolved
disagreement. Do not equate consensus with truth. Distinguish unsupported,
already addressed, and scientifically implausible. Cite decisive agent
arguments and source references. Preserve candidate IDs. Do not invent papers.

Return ONLY JSON:
{{
 "decisions":[
  {{"target_id":"","decision":"retain|revise|combine|reject|hold",
    "reason":"","decisive_arguments":[],"merged_ids":[],
    "revised_text":"","remaining_uncertainties":[]}}
 ],
 "round_summary":""
}}

CANDIDATES:
{_compact(candidates)}

ARGUMENTS THIS ROUND:
{_compact(actions)}
"""


def _run_debate(llm, topic, kind, candidates, verification, model_name, prices,
                history, usage_log):
    """Four independent sequential debate agents, then one adjudicator per round."""
    all_rounds, rejected = [], []
    for round_no in range(1, DEBATE_ROUNDS + 1):
        active = [x for x in candidates if x.get("status") not in ("rejected", "merged")]
        if not active:
            break
        print(f"[DEBATE] {kind}: round {round_no}/{DEBATE_ROUNDS}.")
        actions, prior = [], all_rounds

        for perspective in PERSPECTIVES:
            prompt = _debate_prompt(
                topic, kind, perspective, round_no, active, prior, verification
            )
            result = _call(
                llm, prompt, stage=f"{kind}_debate",
                agent=f"{perspective.title()} Debate Agent",
                model_name=model_name, prices=prices, history=history,
                usage_log=usage_log, round_no=round_no,
            )
            if result is None:
                continue
            raw, _ = result
            parsed = _parsed_event(history, raw)
            if parsed:
                role_actions = parsed.get("actions", [])
                for action in role_actions:
                    if isinstance(action, dict):
                        action["agent"] = perspective
                        action["round"] = round_no
                        actions.append(action)
                history[-1]["action_summary"] = f"{len(role_actions)} action(s)."

        decisions = []
        if actions:
            prompt = _adjudicator_prompt(topic, kind, round_no, active, actions)
            result = _call(
                llm, prompt, stage=f"{kind}_adjudication",
                agent=f"{kind.title()} Debate Adjudicator",
                model_name=model_name, prices=prices, history=history,
                usage_log=usage_log, round_no=round_no,
            )
            if result is not None:
                raw, _ = result
                parsed = _parsed_event(history, raw)
                if parsed:
                    decisions = parsed.get("decisions", [])
                    history[-1]["action_summary"] = f"Decided {len(decisions)} candidate(s)."

        by_id = {
            d.get("target_id"): d for d in decisions
            if isinstance(d, dict) and d.get("target_id")
        }
        for candidate in active:
            candidate_actions = [a for a in actions if a.get("target_id") == candidate["id"]]
            decision = by_id.get(candidate["id"])
            candidate["debate_history"].append({
                "round": round_no, "actions": candidate_actions, "decision": decision,
            })
            if not decision:
                candidate["status"] = "contested"
                continue
            choice = decision.get("decision", "hold")
            candidate["last_decision"] = decision
            if choice == "reject":
                candidate["status"] = "rejected"
                candidate["rejection_reason"] = decision.get("reason", "")
                rejected.append(candidate)
            elif choice == "combine":
                candidate["status"] = "merged"
                candidate["merged_ids"] = decision.get("merged_ids", [])
            elif choice == "revise" and decision.get("revised_text"):
                key = "gap" if kind == "research_gap" else "hypothesis"
                candidate["original_text"] = candidate.get(key)
                candidate[key] = decision["revised_text"]
                candidate["status"] = "revised"
            elif choice == "hold":
                candidate["status"] = "contested"
            else:
                candidate["status"] = "retained"

        all_rounds.append({"round": round_no, "actions": actions, "decisions": decisions})
        history.append({
            "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
            "stage": f"{kind}_state_update", "agent": "Debate Orchestrator",
            "round": round_no, "status": "success",
            "message": (
                f"After round {round_no}: "
                f"{sum(x.get('status') not in ('rejected', 'merged') for x in candidates)} "
                f"active; {len(rejected)} rejected/merged."
            ),
        })

    active = [x for x in candidates if x.get("status") not in ("rejected", "merged")]
    return active, rejected, all_rounds


def _hypothesis_prompt(topic, additional, perspective, gaps, papers):
    guidance = {
        "theoretical": "derive mechanisms, physical relationships and falsifiable predictions",
        "computational": "propose algorithmic, numerical, simulation-based or code-testable hypotheses",
        "observational": "propose hypotheses with measurable empirical/observational consequences",
        "experimental": "propose controlled tests, including laboratory or computational experiments",
    }[perspective]
    return f"""
ROLE: Independent {perspective.title()} Hypothesis Generator
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
PERSPECTIVE: {guidance}

Generate distinct hypotheses from surviving research gaps. Work independently.
A hypothesis must be specific and falsifiable. One gap may yield multiple
hypotheses; a hypothesis may address multiple gaps. Include its mechanism,
rationale, paper evidence/page/section, testable prediction, practical test,
assumptions, counterevidence and related gap IDs. Do not claim novelty beyond
the supplied papers; external verification follows.

Return ONLY JSON:
{{"perspective":"{perspective}","hypotheses":[
 {{"hypothesis":"","rationale":"","supporting_papers":[],"evidence":[],
   "testable_prediction":"","proposed_test":"","caveats":"",
   "related_gap_ids":[],"confidence":"low|medium|high"}}
]}}

SURVIVING GAPS:
{_compact(gaps)}

PAPER ANALYSES:
{_compact(papers)}
"""


def _curator_prompt(topic, gaps, hypotheses, rejected_gaps, rejected_hypotheses):
    return f"""
ROLE: Final Scientific Curator
TOPIC: {topic}

Produce separate ranked research-gap and hypothesis lists. Rank by significance,
novelty relative to available evidence, feasibility, testability and grounding.
Rank is not certainty. Preserve unresolved disagreement; do not force consensus.
Do not reintroduce rejected candidates. Keep contested candidates with a
qualification. Preserve paper filenames, external citations and gap links.

Return ONLY JSON:
{{
 "historical_analysis":"",
 "research_gaps":[
  {{"id":"","rank":1,"gap":"","why_it_matters":"","supporting_papers":[],
    "external_sources":[],"external_status":"","debate_status":"",
    "remaining_uncertainties":[]}}
 ],
 "hypotheses":[
  {{"id":"","rank":1,"hypothesis":"","rationale":"","supporting_papers":[],
    "external_sources":[],"related_gap_ids":[],"testable_prediction":"",
    "proposed_test":"","caveats":"","debate_status":"",
    "remaining_uncertainties":[]}}
 ]
}}

SURVIVING GAPS:
{_compact(gaps)}
SURVIVING HYPOTHESES:
{_compact(hypotheses)}
REJECTED GAPS (audit only):
{_compact(rejected_gaps)}
REJECTED HYPOTHESES (audit only):
{_compact(rejected_hypotheses)}
"""


def _format_gap(item):
    if not isinstance(item, dict):
        return str(item)
    suffix = []
    if item.get("supporting_papers"):
        suffix.append("Papers: " + ", ".join(map(str, item["supporting_papers"])))
    if item.get("external_sources"):
        suffix.append("External: " + "; ".join(
            x.get("title", x.get("url", "")) if isinstance(x, dict) else str(x)
            for x in item["external_sources"]
        ))
    text = f"{item.get('id', '')}: {item.get('gap', '')}"
    return text + (f" [{' | '.join(suffix)}]" if suffix else "")


def _format_history(topic, events):
    lines = [
        "=" * 88, "ATR MULTI-AGENT DEBATE — INFERENCE HISTORY",
        f"Topic: {topic}", f"Generated: {_now()}", "=" * 88, "",
    ]
    for event in events:
        heading = (
            f"[{event.get('event_id', '')}] "
            f"{event.get('stage', 'event').replace('_', ' ').upper()} | "
            f"{event.get('agent', 'Unknown agent')}"
        )
        if event.get("round") is not None:
            heading += f" | Round {event['round']}"
        lines.extend([heading, "-" * min(len(heading), 88)])
        if event.get("paper"):
            lines.append(f"Paper: {event['paper']}")
        if event.get("status"):
            lines.append(f"Status: {event['status']}")
        if event.get("message"):
            lines.append(f"Decision / note: {event['message']}")
        if event.get("action_summary"):
            lines.append(f"Actions: {event['action_summary']}")
        if event.get("error"):
            lines.append(f"Error: {event['error']}")
        if event.get("search_warning"):
            lines.append(f"Search warning: {event['search_warning']}")
        for source in event.get("web_sources", []):
            lines.append(f"Web source: {source.get('title')} — {source.get('url')}")
        if event.get("response"):
            lines.extend(["", "Agent output:", event["response"]])
        lines.append("")
    return "\n".join(lines)


def run_multi_debate(
    llm, topic, additional_prompt, pdf_paths, model_name,
    price_per_million_tokens=None,
):
    """
    Multi-agent entry point matching main.py's single-agent input contract.
    Returns separate research gaps/hypotheses, full provenance, usage and logs.
    Does not write files; main.py owns all output writing.
    """
    global _last_request_completed_at
    _last_request_completed_at = None

    if not topic or not str(topic).strip():
        raise ValueError("topic cannot be empty.")
    pdf_paths = [Path(p) for p in pdf_paths]
    if not pdf_paths:
        raise ValueError("pdf_paths must contain at least one PDF.")

    prices = price_per_million_tokens or {}
    started = time.perf_counter()
    history, api_usage, paper_analyses = [], [], []

    # Google Search grounding is used only by the external literature verifier.
    search_llm = None
    try:
        search_llm = llm.bind_tools([{"google_search": {}}])
        print("[WEB] Google Search grounding enabled.")
    except Exception as exc:
        print(f"[WEB WARNING] Google Search grounding unavailable: {exc}")

    # 1. Each PDF is read independently; requests are sequential.
    print(f"[MULTI] Analysing {len(pdf_paths)} papers sequentially.")
    for index, paper in enumerate(pdf_paths, start=1):
        print(f"[PAPER] {paper.name} ({index}/{len(pdf_paths)}).")
        result = _call(
            llm, _reader_prompt(topic, additional_prompt, paper),
            stage="paper_analysis", agent="Literature Analyst",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, paper=paper,
        )
        if result is None:
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": "paper_analysis_skipped", "agent": "Orchestrator",
                "paper": str(paper.resolve()), "status": "warning",
                "message": "Paper request failed; excluded from synthesis.",
            })
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        paper_analyses.append({
            "paper": str(paper.resolve()), "paper_filename": paper.name,
            "analysis": parsed if parsed is not None else raw,
        })
        print(f"[PAPER] Completed {paper.name}.")

    if not paper_analyses:
        raise RuntimeError("No paper could be analysed successfully.")

    # 2. Four independent perspectives identify research gaps.
    gap_candidates = []
    for perspective in PERSPECTIVES:
        print(f"[GAPS] {perspective.title()} perspective.")
        result = _call(
            llm, _perspective_prompt(
                topic, additional_prompt, perspective, paper_analyses
            ),
            stage="research_gap_generation",
            agent=f"{perspective.title()} Gap Analyst",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage,
        )
        if result is None:
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        if parsed:
            items = _assign_ids(parsed.get("research_gaps", []), "G", perspective)
            gap_candidates.extend(items)
            history[-1]["action_summary"] = (
                f"Independently proposed {len(items)} research gap(s)."
            )

    # 3. Search external literature to verify candidate gaps.
    gap_verification, gap_web_sources = {}, []
    if gap_candidates:
        print("[WEB] Verifying research gaps against external literature.")
        result = _call(
            llm, _verify_prompt(topic, gap_candidates, "research gaps"),
            stage="research_gap_web_verification",
            agent="External Literature Verification Agent",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, use_search=True, search_llm=search_llm,
        )
        if result is not None:
            raw, gap_web_sources = result
            gap_verification = _parsed_event(history, raw) or {}
        _apply_verification(gap_candidates, gap_verification, gap_web_sources)

    # 4. Debate and adjudicate gaps for three rounds.
    active_gaps, rejected_gaps, gap_debate = _run_debate(
        llm, topic, "research_gap", gap_candidates, gap_verification,
        model_name, prices, history, api_usage,
    )

    # 5. Four independent perspectives generate hypotheses from surviving gaps.
    hypothesis_candidates = []
    for perspective in PERSPECTIVES:
        if not active_gaps:
            break
        print(f"[HYPOTHESES] {perspective.title()} perspective.")
        result = _call(
            llm, _hypothesis_prompt(
                topic, additional_prompt, perspective, active_gaps, paper_analyses
            ),
            stage="hypothesis_generation",
            agent=f"{perspective.title()} Hypothesis Generator",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage,
        )
        if result is None:
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        if parsed:
            items = _assign_ids(parsed.get("hypotheses", []), "H", perspective)
            hypothesis_candidates.extend(items)
            history[-1]["action_summary"] = (
                f"Independently proposed {len(items)} hypothesis/hypotheses."
            )

    # 6. External literature verification for hypotheses.
    hypothesis_verification, hypothesis_web_sources = {}, []
    if hypothesis_candidates:
        print("[WEB] Verifying hypotheses against external literature.")
        result = _call(
            llm, _verify_prompt(
                topic, hypothesis_candidates, "candidate hypotheses"
            ),
            stage="hypothesis_web_verification",
            agent="External Literature Verification Agent",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, use_search=True, search_llm=search_llm,
        )
        if result is not None:
            raw, hypothesis_web_sources = result
            hypothesis_verification = _parsed_event(history, raw) or {}
        _apply_verification(
            hypothesis_candidates, hypothesis_verification, hypothesis_web_sources
        )

    # 7. Debate and adjudicate hypotheses for three rounds.
    active_hypotheses, rejected_hypotheses, hypothesis_debate = _run_debate(
        llm, topic, "hypothesis", hypothesis_candidates,
        hypothesis_verification, model_name, prices, history, api_usage,
    )

    # 8. Final curator keeps gaps and hypotheses as separate ranked lists.
    print("[FINAL] Curating separate research-gap and hypothesis lists.")
    result = _call(
        llm, _curator_prompt(
            topic, active_gaps, active_hypotheses,
            rejected_gaps, rejected_hypotheses,
        ),
        stage="final_curation", agent="Final Scientific Curator",
        model_name=model_name, prices=prices, history=history,
        usage_log=api_usage,
    )
    final_data = {}
    if result is not None:
        raw, _ = result
        final_data = _parsed_event(history, raw) or {}

    final_gaps = final_data.get("research_gaps") or active_gaps
    final_hypotheses = final_data.get("hypotheses") or active_hypotheses
    historical_analysis = final_data.get("historical_analysis", "")

    successful = [x for x in api_usage if x["status"] == "success"]
    costs = [
        x["estimated_cost_usd"] for x in successful
        if x["estimated_cost_usd"] is not None
    ]
    usage_summary = {
        "api_calls_logged": len(api_usage),
        "successful_calls": len(successful),
        "failed_calls": len(api_usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "note": "Usage covers calls recorded by this pipeline, not account-wide quota.",
    }

    history.append({
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": "final_result", "agent": "Orchestrator", "status": "success",
        "message": (
            f"Final output: {len(final_gaps)} research gap(s), "
            f"{len(final_hypotheses)} hypothesis/hypotheses."
        ),
    })
    history_text = _format_history(topic, history)

    return {
        "agent_params": {
            "mode": "multi_debate",
            "topic": topic,
            "additional_prompt": additional_prompt,
            "model": model_name,
            "papers": [str(p.resolve()) for p in pdf_paths],
            "perspectives": list(PERSPECTIVES),
            "debate_rounds": DEBATE_ROUNDS,
            "execution": "sequential independent agent calls; no concurrent requests",
            "pause_after_response_seconds": PAUSE_SEC,
        },
        "paper_analyses": paper_analyses,
        "historical_analysis": historical_analysis,
        "research_gaps": [_format_gap(x) for x in final_gaps],
        "research_gap_records": final_gaps,
        "hypotheses": final_hypotheses,
        "rejected_research_gaps": rejected_gaps,
        "rejected_hypotheses": rejected_hypotheses,
        "debate_summaries": {
            "research_gaps": gap_debate,
            "hypotheses": hypothesis_debate,
        },
        "web_verification": {
            "research_gaps": gap_verification,
            "hypotheses": hypothesis_verification,
        },
        "usage_summary": usage_summary,
        "api_usage": api_usage,
        "inference_history": history,
        "inference_history_text": history_text,
    }
