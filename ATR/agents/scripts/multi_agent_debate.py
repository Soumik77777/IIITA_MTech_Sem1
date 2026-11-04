"""ATR adaptive multi-agent research-gap and hypothesis pipeline."""
import base64
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

PAUSE_SEC = 5
MAX_RETRIES = 3
DEBATE_ROUNDS = 3
EXAMPLE_PERSPECTIVES = {
    "theoretical": "Explanations, assumptions, mathematical consistency, guarantees and predictions.",
    "computational": "Algorithms, numerical methods, simulations, complexity and reproducibility.",
    "observational": "Measurements, data limitations, parameter degeneracies and model-observation mismatch.",
    "experimental": "Testability and controlled laboratory, physical, numerical or code-based experiments.",
}
_last_request_completed_at = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(x.get("text")) if isinstance(x, dict) and x.get("text") is not None
            else str(x) for x in content
        ).strip()
    return str(content).strip()


def _parse(raw):
    """Parse JSON with recovery for invalid backslash escapes in model output."""
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip(), flags=re.I | re.S)
    candidates = [raw]

    # Extract the first balanced JSON object/array rather than slicing from the
    # first opening brace to the final closing brace (which may include prose).
    for left, right in (("{", "}"), ("[", "]")):
        start = raw.find(left)
        if start < 0:
            continue
        depth, quoted, escaped = 0, False, False
        for i in range(start, len(raw)):
            char = raw[i]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == left:
                depth += 1
            elif char == right:
                depth -= 1
                if depth == 0:
                    candidates.append(raw[start:i + 1])
                    break

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            repaired = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                continue
    return None


def _dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _wait():
    global _last_request_completed_at
    if _last_request_completed_at is not None:
        delay = PAUSE_SEC - (time.monotonic() - _last_request_completed_at)
        if delay > 0:
            print(f"[RATE LIMIT] Waiting {delay:.1f}s.")
            time.sleep(delay)


def _call(llm, prompt, *, stage, agent, model_name, prices, history, usage_log,
          paper_path=None, round_no=None):
    global _last_request_completed_at
    event = {
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": stage, "agent": agent, "round": round_no,
        "paper_loc": str(Path(paper_path).resolve()) if paper_path else None,
        "prompt": prompt, "status": "started",
    }
    history.append(event)
    try:
        if paper_path:
            p = Path(paper_path).resolve()
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "media", "mime_type": "application/pdf",
                 "data": base64.b64encode(p.read_bytes()).decode("ascii")},
            ])
        else:
            message = HumanMessage(content=prompt)
    except Exception as exc:
        event.update(status="error", error=f"{type(exc).__name__}: {exc}")
        return None

    for attempt in range(1, MAX_RETRIES + 1):
        _wait()
        started = time.perf_counter()
        try:
            response = llm.invoke([message])
            runtime = round(time.perf_counter() - started, 3)
            _last_request_completed_at = time.monotonic()
            usage = getattr(response, "usage_metadata", None) or {}
            inp, out = usage.get("input_tokens"), usage.get("output_tokens")
            total = usage.get("total_tokens")
            if total is None and inp is not None and out is not None:
                total = inp + out
            cost = None
            if inp is not None and out is not None and prices.get("input") is not None and prices.get("output") is not None:
                cost = (inp * prices["input"] + out * prices["output"]) / 1_000_000
            usage_log.append({
                "timestamp_utc": _now(), "stage": stage, "agent": agent,
                "round": round_no, "paper_loc": event["paper_loc"],
                "model": model_name, "attempt": attempt, "status": "success",
                "runtime_seconds": runtime, "input_tokens": inp,
                "output_tokens": out, "total_tokens": total,
                "estimated_cost_usd": cost, "error": None,
            })
            raw = _text(response.content)
            parsed = _parse(raw)
            event.update(status="success", response=raw, parsed_output=parsed,
                         runtime_seconds=runtime, attempts=attempt)
            if parsed is None:
                event["parse_warning"] = "Invalid JSON; raw response retained."
            return parsed
        except Exception as exc:
            runtime = round(time.perf_counter() - started, 3)
            _last_request_completed_at = time.monotonic()
            error = f"{type(exc).__name__}: {exc}"
            usage_log.append({
                "timestamp_utc": _now(), "stage": stage, "agent": agent,
                "round": round_no, "paper_loc": event["paper_loc"],
                "model": model_name, "attempt": attempt, "status": "error",
                "runtime_seconds": runtime, "input_tokens": None,
                "output_tokens": None, "total_tokens": None,
                "estimated_cost_usd": None, "error": error,
            })
            retryable = any(x in str(exc).lower() for x in
                            ("429", "resource_exhausted", "rate limit", "503",
                             "service unavailable", "502", "504"))
            if retryable and attempt < MAX_RETRIES:
                time.sleep(PAUSE_SEC * (2 ** (attempt - 1)))
                continue
            event.update(status="error", error=error, runtime_seconds=runtime,
                         attempts=attempt)
            print(f"[ERROR] {agent}: {error}")
            return None
    return None


def _paper_cards(papers):
    cards = []
    for p in papers:
        a = p["analysis"]
        cards.append({
            "paper_id": p["paper_id"], "paper_title": a.get("paper_title", p["paper_filename"]),
            "authors_year": a.get("authors_year", ""),
            "research_question": a.get("research_question", ""),
            "methods": a.get("methods", []), "main_findings": a.get("main_findings", []),
            "assumptions": a.get("assumptions", []),
            "limitations_explicit": a.get("limitations_explicit", []),
            "potential_open_questions": a.get("potential_open_questions", []),
            "paper_loc": p["paper_loc"],
        })
    return cards


def _normal_refs(refs, valid_ids):
    output = {}
    for ref in refs if isinstance(refs, list) else []:
        if isinstance(ref, str):
            pid, sections = ref, []
        elif isinstance(ref, dict):
            pid = ref.get("paper_id") or ref.get("id")
            sections = ref.get("sections", [])
            if isinstance(sections, str):
                sections = [sections]
        else:
            continue
        if pid not in valid_ids:
            continue
        entry = output.setdefault(pid, {"paper_id": pid, "sections": []})
        entry["sections"] = list(dict.fromkeys(entry["sections"] + [str(s) for s in sections if s]))
    return list(output.values())


def _normal_related(items, valid_ids):
    result = []
    for x in items if isinstance(items, list) else []:
        if isinstance(x, dict) and (x.get("paper_id") or x.get("id")) in valid_ids:
            result.append({
                "paper_id": x.get("paper_id") or x.get("id"),
                "sections": x.get("sections", []) or [],
                "relation": x.get("relation", "mentions"),
                "explanation": x.get("explanation", ""),
            })
    return result


def _reader_prompt(topic, additional, paper_id, path):
    return f"""
ROLE: Literature Reader
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
PAPER ID: {paper_id}
PAPER FILE: {Path(path).name}
Read only the attached paper. Separate explicit statements from inference.
Capture section/page references wherever possible. A limitation is not
automatically a research gap. Return only valid JSON:
{{
 "paper_title":"","authors_year":"","research_question":"","context":"",
 "methods":[],"main_findings":[],"assumptions":[],"limitations_explicit":[],
 "potential_open_questions":[{{"question":"","why_unresolved":"","evidence":"","sections":[]}}],
 "candidate_hypotheses":[{{"hypothesis":"","rationale":"","evidence":"","sections":[]}}]
}}
Do not claim novelty beyond this paper.
"""


def _finder_prompt(topic, additional, cards):
    return f"""
ROLE: Topic-Adaptive Perspective Finder
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
Discover perspectives that collectively cover all plausible research-generation
areas for this topic, including areas likely to be found without assigned roles.
Minimize overlap. Examples below are illustrative, not fixed defaults:
{_dump(EXAMPLE_PERSPECTIVES)}
Return a compact set of distinct perspectives. For each provide name,
description, excludes, owned_by, boundary_rule and rationale. Explicitly state
which perspective owns overlapping/root-cause areas. Do not impose a fixed
number; prioritize broad coverage with minimum overlap.
Return only JSON:
{{"perspectives":[{{"name":"","description":"","excludes":[],"owned_by":[],
"boundary_rule":"","rationale":""}}],"coverage_check":"","overlap_check":""}}
PAPER SUMMARIES:
{_dump(cards)}
"""


def _gap_prompt(topic, additional, perspective, cards):
    return f"""
ROLE: Research-Gap Generator
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
PERSPECTIVE: {_dump(perspective)}
Identify evidence-supported explicit or inferred gaps within this perspective.
Respect its exclusions and ownership boundaries. Each gap must explain what is
known, what remains unknown and why it matters. Cite direct evidence and
supporting papers using only supplied paper IDs. Use section references where
possible; sections may be empty but paper IDs must be valid.
Return only JSON:
{{"perspective":"{perspective['name']}","research_gaps":[{{
"gap":"","why_it_matters":"","what_is_known":"","what_remains_unknown":"",
"gap_type":"explicit|inferred","confidence":"low|medium|high",
"supporting_papers":[{{"paper_id":"P001","sections":[]}}],
"evidence":[{{"paper_id":"P001","section":"","evidence":""}}]
}}]}}
PAPER SUMMARIES:
{_dump(cards)}
"""


def _curator_prompt(topic, candidates, cards):
    return f"""
ROLE: Research-Gap Curator and Corpus Analyser
TOPIC: {topic}
First merge only genuinely repetitive gaps (same question and substantially
same resolution); do not create umbrella gaps. Reject duplicates/non-gaps.
Do not rank. Keep one existing ID for a merge and list absorbed IDs.
Then independently check EVERY candidate against EVERY paper summary,
including papers not cited by that candidate. Add related_papers with relation
addresses, contradicts, extends or mentions, plus sections and explanation.
Corpus-only: never claim novelty; say "not found as addressed in this corpus".
Every input ID must be retained, merged or rejected; never silently drop.
Preserve/union supporting_papers, evidence and origin perspectives.
Return only JSON:
{{"research_gaps":[{{"id":"G001","decision":"retain|merge|reject","merged_ids":[],
"reason":"","gap":"","why_it_matters":"","what_is_known":"",
"what_remains_unknown":"","gap_type":"","confidence":"",
"origin_perspectives":[],"supporting_papers":[],"related_papers":[],"evidence":[]}}],
"rejected":[{{"id":"G000","reason":""}}],"curation_summary":""}}
CANDIDATE GAPS:
{_dump(candidates)}
ALL PAPER SUMMARIES:
{_dump(cards)}
"""


def _challenger_prompt(topic, kind, rnd, records, perspectives, cards):
    return f"""
ROLE: Scientific Challenger
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{DEBATE_ROUNDS}
In ONE call, apply all perspective lenses below to every record. It is not
mandatory to propose changes. Only suggest changes when necessary; do not
manufacture disagreement. Categories: unsupported_by_cited_papers,
already_addressed, infeasible, vague, non_falsifiable. Cite corpus paper IDs
and sections. Corpus-only, no web search or outside knowledge.
Return only JSON:
{{"proposed_changes":[{{"target_id":"","action":"revise|reject|merge|retain",
"category":"unsupported_by_cited_papers|already_addressed|infeasible|vague|non_falsifiable",
"perspective":"","argument":"","evidence":[],"paper_references":[],
"proposed_revision":"","merge_with":[]}}],"no_change_reason":""}}
PERSPECTIVES: {_dump(perspectives)}
RECORDS: {_dump(records)}
PAPER SUMMARIES: {_dump(cards)}
"""


def _defender_prompt(topic, kind, rnd, records, challenges, cards):
    return f"""
ROLE: Scientific Defender
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{DEBATE_ROUNDS}
For every challenge, defend if evidence supports the record, concede if correct,
or partially concede. Do not defend merely for debate. Suggest revisions only
when needed. Cite corpus paper IDs and sections. Preserve IDs and provenance.
Return only JSON:
{{"responses":[{{"target_id":"","position":"defend|concede|partially_concede",
"response":"","evidence":[],"paper_references":[],"proposed_revision":""}}],
"overall_response":""}}
RECORDS: {_dump(records)}
CHALLENGES: {_dump(challenges)}
PAPER SUMMARIES: {_dump(cards)}
"""


def _adjudicator_prompt(topic, kind, rnd, records, challenges, defences):
    return f"""
ROLE: Scientific Adjudicator
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{DEBATE_ROUNDS}
Decide each affected record: retain, revise, merge or reject. For a revision,
rewrite the COMPLETE record including supporting_papers, related_papers and
evidence. Never change or renumber IDs. A merge keeps one existing ID and
lists absorbed IDs. Do not silently drop records. Preserve uncertainties.
Return only JSON:
{{"decisions":[{{"target_id":"","decision":"retain|revise|merge|reject",
"reason":"","merged_ids":[],"revised_record":{{"id":"",
"gap_or_hypothesis_text":"","why_it_matters":"","what_is_known":"",
"what_remains_unknown":"","rationale":"","testable_prediction":"",
"proposed_test":"","supporting_papers":[],"related_papers":[],"evidence":[]}},
"remaining_uncertainties":[]}}],"round_summary":""}}
RECORDS: {_dump(records)}
CHALLENGES: {_dump(challenges)}
DEFENCES: {_dump(defences)}
"""


def _hypothesis_prompt(topic, additional, perspective, gaps, cards):
    return f"""
ROLE: Scientific Hypothesis Generator
TOPIC: {topic}; USER INSTRUCTIONS: {additional or "None"}
PERSPECTIVE: {_dump(perspective)}
Generate testable hypotheses grounded in the final gaps. Each must cite one or
more originating gap IDs, and attach supporting paper IDs/sections and direct
evidence. Do not generate unrelated hypotheses or claim proof.
Return only JSON:
{{"perspective":"{perspective['name']}","hypotheses":[{{
"hypothesis":"","rationale":"","testable_prediction":"","proposed_test":"",
"originating_gap_ids":["G001"],"supporting_papers":[],"related_papers":[],"evidence":[]
}}]}}
FINAL GAPS: {_dump(gaps)}
PAPER SUMMARIES: {_dump(cards)}
"""


def _final_prompt(topic, gaps, hypotheses):
    return f"""
ROLE: Final Output Curator
TOPIC: {topic}
Prepare final lists; do not rank. Remove only substantive duplicates. On merge,
keep an existing ID and list absorbed IDs. Never renumber IDs. Preserve
originating gap IDs, paper/section references, evidence and debate history.
Every input ID must be retained or explicitly listed as merged/rejected.
Return only JSON:
{{"research_gaps":[],"hypotheses":[],"merged_or_rejected":[],"curation_summary":""}}
GAPS: {_dump(gaps)}
HYPOTHESES: {_dump(hypotheses)}
"""


def _new_records(items, prefix, start, perspective, valid_ids):
    result = []
    n = start
    key = "gap" if prefix == "G" else "hypothesis"
    for raw in items if isinstance(items, list) else []:
        if not isinstance(raw, dict) or not raw.get(key):
            continue
        item = dict(raw)
        item.update({
            "id": f"{prefix}{n:03d}", "origin_perspective": perspective,
            "status": "candidate",
            "supporting_papers": _normal_refs(item.get("supporting_papers"), valid_ids),
            "related_papers": _normal_related(item.get("related_papers"), valid_ids),
            "debate_history": [],
        })
        item.setdefault("evidence", [])
        result.append(item)
        n += 1
    return result, n


def _merge_refs(*groups):
    return _normal_refs(
        [ref for group in groups for ref in (group or [])], 
        {ref.get("paper_id") for group in groups for ref in (group or [])
         if isinstance(ref, dict) and ref.get("paper_id")}
    )


def _apply_initial_curation(records, parsed, valid_ids, history):
    by_id = {x["id"]: x for x in records}
    active, rejected, accounted = [], [], set()
    for decision in parsed.get("research_gaps", []) if isinstance(parsed, dict) else []:
        if not isinstance(decision, dict):
            continue
        rid = decision.get("id")
        original = by_id.get(rid)
        if not original or rid in accounted:
            continue
        accounted.add(rid)
        action = decision.get("decision", "retain")
        if action == "reject":
            original.update(status="rejected", rejection_reason=decision.get("reason", ""))
            rejected.append(original)
            continue
        if action == "merge":
            absorbed_ids = decision.get("merged_ids", [])
            original["merged_ids"] = absorbed_ids
            original["merge_reason"] = decision.get("reason", "")
            for mid in absorbed_ids:
                absorbed = by_id.get(mid)
                if absorbed:
                    original["supporting_papers"] = _merge_refs(
                        original.get("supporting_papers"), absorbed.get("supporting_papers"))
                    original["related_papers"] += absorbed.get("related_papers", [])
                    absorbed.update(status="merged", merged_into=rid)
                    accounted.add(mid)
        for field in ("gap", "why_it_matters", "what_is_known",
                      "what_remains_unknown", "gap_type", "confidence", "evidence"):
            if decision.get(field) is not None:
                original[field] = decision[field]
        original["origin_perspectives"] = decision.get(
            "origin_perspectives", [original.get("origin_perspective")])
        original["supporting_papers"] = _merge_refs(
            original.get("supporting_papers"),
            _normal_refs(decision.get("supporting_papers"), valid_ids))
        original["related_papers"] += _normal_related(decision.get("related_papers"), valid_ids)
        original["status"] = "candidate"
        active.append(original)

    for item in parsed.get("rejected", []) if isinstance(parsed, dict) else []:
        if isinstance(item, dict) and item.get("id") in by_id and item["id"] not in accounted:
            rec = by_id[item["id"]]
            rec.update(status="rejected", rejection_reason=item.get("reason", ""))
            rejected.append(rec)
            accounted.add(item["id"])

    # Model omission is never allowed to silently delete a candidate.
    for rec in records:
        if rec["id"] not in accounted and rec.get("status") != "merged":
            rec["status"] = "candidate"
            active.append(rec)
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": "curation_integrity_warning", "agent": "Orchestrator",
                "status": "warning", "message": f"{rec['id']} omitted; retained.",
            })
    return active, rejected


def _active(records):
    return [x for x in records if x.get("status") not in ("rejected", "merged")]


def _run_debate(llm, topic, kind, records, perspectives, cards, model_name,
                prices, history, usage, valid_ids):
    rounds, rejected = [], []
    for rnd in range(1, DEBATE_ROUNDS + 1):
        current = _active(records)
        if not current:
            break
        print(f"[DEBATE] {kind}, round {rnd}/{DEBATE_ROUNDS}")
        challenges = _call(
            llm, _challenger_prompt(topic, kind, rnd, current, perspectives, cards),
            stage=f"{kind}_challenger", agent=f"{kind.title()} Challenger",
            model_name=model_name, prices=prices, history=history,
            usage_log=usage, round_no=rnd,
        ) or {}
        changes = challenges.get("proposed_changes", [])
        if not isinstance(changes, list) or not changes:
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": f"{kind}_debate_terminated", "agent": "Orchestrator",
                "round": rnd, "status": "success",
                "message": "No challenger changes; defender, adjudicator and later rounds skipped.",
            })
            rounds.append({"round": rnd, "challenges": [], "terminated": True,
                           "reason": challenges.get("no_change_reason", "")})
            break

        defences = _call(
            llm, _defender_prompt(topic, kind, rnd, current, changes, cards),
            stage=f"{kind}_defender", agent=f"{kind.title()} Defender",
            model_name=model_name, prices=prices, history=history,
            usage_log=usage, round_no=rnd,
        ) or {}
        responses = defences.get("responses", [])
        adjudication = _call(
            llm, _adjudicator_prompt(topic, kind, rnd, current, changes, responses),
            stage=f"{kind}_adjudication", agent=f"{kind.title()} Adjudicator",
            model_name=model_name, prices=prices, history=history,
            usage_log=usage, round_no=rnd,
        ) or {}
        decisions = adjudication.get("decisions", [])
        by_id = {x["id"]: x for x in current}
        for decision in decisions if isinstance(decisions, list) else []:
            if not isinstance(decision, dict):
                continue
            rid = decision.get("target_id")
            rec = by_id.get(rid)
            if not rec:
                continue
            decision["round"] = rnd
            rec.setdefault("debate_history", []).append({
                "round": rnd,
                "challenge": [x for x in changes if x.get("target_id") == rid],
                "defence": [x for x in responses if x.get("target_id") == rid],
                "decision": decision,
            })
            action = decision.get("decision", "retain")
            rec["last_decision"] = decision
            if action == "reject":
                rec.update(status="rejected", rejection_reason=decision.get("reason", ""))
                rejected.append(rec)
            elif action == "merge":
                rec.update(status="merged", merged_ids=decision.get("merged_ids", []))
                for mid in rec["merged_ids"]:
                    if mid in by_id:
                        by_id[mid].update(status="merged", merged_into=rid)
                        rec["supporting_papers"] = _merge_refs(
                            rec.get("supporting_papers"), by_id[mid].get("supporting_papers"))
            elif action == "revise":
                revised = decision.get("revised_record") or {}
                key = "gap" if kind == "research_gap" else "hypothesis"
                new_text = revised.get("gap_or_hypothesis_text") or revised.get(key)
                if new_text:
                    rec.setdefault("previous_versions", []).append(rec.get(key))
                    rec[key] = new_text
                for field in ("why_it_matters", "what_is_known", "what_remains_unknown",
                              "rationale", "testable_prediction", "proposed_test", "evidence"):
                    if revised.get(field) is not None:
                        rec[field] = revised[field]
                rec["supporting_papers"] = _merge_refs(
                    rec.get("supporting_papers"),
                    _normal_refs(revised.get("supporting_papers"), valid_ids))
                rec["related_papers"] += _normal_related(revised.get("related_papers"), valid_ids)
                rec["status"] = "revised"
            else:
                rec["status"] = "retained"
        rounds.append({
            "round": rnd, "challenges": changes, "defences": responses,
            "decisions": decisions, "round_summary": adjudication.get("round_summary", ""),
            "terminated": False,
        })
    return _active(records), rejected, rounds


def _history_text(topic, events):
    lines = ["=" * 80, "ATR ADAPTIVE MULTI-AGENT INFERENCE HISTORY",
             f"Topic: {topic}", f"Generated: {_now()}", "=" * 80, ""]
    for e in events:
        head = f"[{e.get('event_id')}] {e.get('stage')} | {e.get('agent')}"
        if e.get("round") is not None:
            head += f" | Round {e['round']}"
        lines += [head, "-" * min(len(head), 80)]
        if e.get("paper_loc"):
            lines.append(f"Paper: {e['paper_loc']}")
        if e.get("status"):
            lines.append(f"Status: {e['status']}")
        if e.get("message"):
            lines.append(e["message"])
        if e.get("error"):
            lines.append(f"Error: {e['error']}")
        if e.get("response"):
            lines += ["", e["response"]]
        lines.append("")
    return "\n".join(lines)


def _format_gap(item):
    refs = []
    for ref in item.get("supporting_papers", []):
        section = ", ".join(ref.get("sections", []))
        refs.append(ref["paper_id"] + (f" ({section})" if section else ""))
    suffix = " [Papers: " + "; ".join(refs) + "]" if refs else ""
    return f"{item.get('id')}: {item.get('gap', '')}{suffix}"


def run_multi_debate(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    """Existing main.py-compatible entry point; returns data and logs only."""
    global _last_request_completed_at
    _last_request_completed_at = None
    if not topic or not str(topic).strip():
        raise ValueError("topic cannot be empty.")
    paths = [Path(p).resolve() for p in pdf_paths]
    if not paths:
        raise ValueError("pdf_paths must contain at least one PDF.")
    prices = price_per_million_tokens or {}
    started = time.perf_counter()
    history, usage, papers = [], [], []

    # 1. Reader: one independent call per paper.
    print(f"[READER] Reading {len(paths)} papers sequentially.")
    for index, path in enumerate(paths, 1):
        pid = f"P{index:03d}"
        parsed = _call(
            llm, _reader_prompt(topic, additional_prompt, pid, path),
            stage="paper_reading", agent="Literature Reader",
            model_name=model_name, prices=prices, history=history,
            usage_log=usage, paper_path=path,
        )
        if not isinstance(parsed, dict):
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": "paper_reading_skipped", "agent": "Orchestrator",
                "paper_id": pid, "paper_loc": str(path), "status": "warning",
                "message": "Paper failed or returned invalid JSON.",
            })
            continue
        papers.append({"paper_id": pid, "paper_loc": str(path),
                       "paper_filename": path.name, "analysis": parsed})
    if not papers:
        raise RuntimeError("No paper could be read successfully.")
    cards = _paper_cards(papers)
    valid_ids = {x["paper_id"] for x in cards}

    # 2. Topic-adaptive perspective finder.
    print("[PERSPECTIVES] Discovering topic-specific perspectives.")
    perspective_data = _call(
        llm, _finder_prompt(topic, additional_prompt, cards),
        stage="perspective_discovery", agent="Topic-Adaptive Perspective Finder",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
    ) or {}
    perspectives = perspective_data.get("perspectives", [])
    if not isinstance(perspectives, list):
        perspectives = []
    perspectives = [p for p in perspectives if isinstance(p, dict)
                    and p.get("name") and p.get("description")]
    if not perspectives:
        raise RuntimeError("Perspective Finder returned no valid perspectives.")

    # 3. Gap generation: one call per discovered perspective; global IDs.
    candidates, next_id = [], 1
    for perspective in perspectives:
        print(f"[GAPS] {perspective['name']}")
        parsed = _call(
            llm, _gap_prompt(topic, additional_prompt, perspective, cards),
            stage="research_gap_generation",
            agent=f"{perspective['name']} Gap Generator",
            model_name=model_name, prices=prices, history=history, usage_log=usage,
        ) or {}
        new, next_id = _new_records(
            parsed.get("research_gaps", []), "G", next_id,
            perspective["name"], valid_ids)
        candidates.extend(new)

    # 4. Curator/analyser checks every candidate against every paper card.
    print("[CURATOR] Curating gaps and checking the complete corpus.")
    curated = _call(
        llm, _curator_prompt(topic, candidates, cards),
        stage="initial_gap_curation_and_corpus_analysis",
        agent="Research-Gap Curator and Corpus Analyser",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
    ) or {}
    gaps, rejected_gaps = _apply_initial_curation(candidates, curated, valid_ids, history)

    # 5. Gap debate.
    gaps, debate_rejected, gap_rounds = _run_debate(
        llm, topic, "research_gap", gaps, perspectives, cards,
        model_name, prices, history, usage, valid_ids)
    rejected_gaps.extend(debate_rejected)

    # 6. Hypothesis generation: one call per perspective, IDs global.
    hypotheses, next_hid = [], 1
    if gaps:
        for perspective in perspectives:
            print(f"[HYPOTHESES] {perspective['name']}")
            parsed = _call(
                llm, _hypothesis_prompt(topic, additional_prompt, perspective, gaps, cards),
                stage="hypothesis_generation",
                agent=f"{perspective['name']} Hypothesis Generator",
                model_name=model_name, prices=prices, history=history, usage_log=usage,
            ) or {}
            new, next_hid = _new_records(
                parsed.get("hypotheses", []), "H", next_hid,
                perspective["name"], valid_ids)
            known = {g["id"] for g in gaps}
            for h in new:
                h["originating_gap_ids"] = [
                    x for x in h.get("originating_gap_ids", []) if x in known]
            hypotheses.extend(new)

    # 7. Hypothesis debate.
    hypotheses, rejected_hypotheses, hypothesis_rounds = _run_debate(
        llm, topic, "hypothesis", hypotheses, perspectives, cards,
        model_name, prices, history, usage, valid_ids)

    # 8. Final curation. Fail-safe preserves IDs and records omitted by curator.
    final_data = _call(
        llm, _final_prompt(topic, gaps, hypotheses),
        stage="final_curation", agent="Final Output Curator",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
    ) or {}

    def final_records(proposed, originals):
        source = {x["id"]: x for x in originals}
        output, seen = [], set()
        for item in proposed if isinstance(proposed, list) else []:
            if not isinstance(item, dict):
                continue
            rid = item.get("id")
            if rid not in source or rid in seen:
                continue
            merged = dict(source[rid])
            merged.update(item)
            merged["id"] = rid
            merged["supporting_papers"] = _merge_refs(
                source[rid].get("supporting_papers"),
                _normal_refs(item.get("supporting_papers"), valid_ids))
            merged["related_papers"] = (
                source[rid].get("related_papers", []) +
                _normal_related(item.get("related_papers"), valid_ids))
            output.append(merged)
            seen.add(rid)
        output.extend(x for x in originals if x["id"] not in seen)
        return output

    final_gaps = final_records(final_data.get("research_gaps"), gaps)
    final_hypotheses = final_records(final_data.get("hypotheses"), hypotheses)

    successful = [x for x in usage if x["status"] == "success"]
    costs = [x["estimated_cost_usd"] for x in successful
             if x["estimated_cost_usd"] is not None]
    summary = {
        "api_calls_logged": len(usage), "successful_calls": len(successful),
        "failed_calls": len(usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "note": "Pipeline usage only; not account-wide quota.",
    }
    history.append({
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": "final_result", "agent": "Orchestrator", "status": "success",
        "message": f"{len(final_gaps)} gaps and {len(final_hypotheses)} hypotheses.",
    })
    return {
        "agent_params": {
            "mode": "adaptive_multi_agent", "topic": topic,
            "additional_prompt": additional_prompt, "model": model_name,
            "papers": [{"paper_id": p["paper_id"], "paper_loc": p["paper_loc"]}
                       for p in papers],
            "perspectives": perspectives, "debate_rounds_max": DEBATE_ROUNDS,
            "debate_termination": "Stop when challenger proposes no changes.",
            "execution": "Sequential API calls; no concurrent requests.",
            "pause_after_response_seconds": PAUSE_SEC, "web_search": False,
        },
        "paper_analyses": papers,
        "perspective_finder_output": perspective_data,
        "research_gaps": [_format_gap(x) for x in final_gaps],
        "research_gap_records": final_gaps,
        "hypotheses": final_hypotheses,
        "rejected_research_gaps": rejected_gaps,
        "rejected_hypotheses": rejected_hypotheses,
        "debate_summaries": {"research_gaps": gap_rounds, "hypotheses": hypothesis_rounds},
        "curation": {"initial": curated,
                     "final_summary": final_data.get("curation_summary", ""),
                     "merged_or_rejected": final_data.get("merged_or_rejected", [])},
        "usage_summary": summary, "api_usage": usage,
        "inference_history": history,
        "inference_history_text": _history_text(topic, history),
    }
