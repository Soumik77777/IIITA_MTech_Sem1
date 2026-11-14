"""Single-LLM research-gap and hypothesis-generation pipeline.

Stages:
1. Read each PDF separately (same reader prompt and schema as the multi-agent pipeline).
2. Iteratively generate ID-numbered research gaps, then generate hypotheses.
3. Up to `max_rounds` rounds of self-critique -> revision by the SAME researcher.
   One round = two calls (critique, then revision). The loop stops early when the
   critique proposes no changes. There are no personas, no defender/adjudicator roles
   and no debate.

Every record keeps its evidence, supporting papers and per-round history. The history is
stored under "debate_history" for schema parity with the multi-agent pipeline
("defence" is always empty here). The initial draft and a snapshot after every round are
also returned, so the full evolution of each record can be reconstructed.

This module returns data and logs; main.py owns file output and the run constants
(max_rounds, pause_sec, max_retries).
"""

import base64
import copy
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

_RETRYABLE_TERMS = (
    "429", "resource_exhausted", "rate limit", "too many requests",
    "503", "service unavailable", "502", "504",
)
_LABELS = {
    "paper_analysis": "PAPER ANALYSIS",
    "research_gap_generation": "GAP GENERATION",
    "hypothesis_generation": "HYPOTHESIS GENERATION",
    "self_critique": "SELF-CRITIQUE",
    "self_critique_revision": "REVISION",
}
_REVISION_FIELDS = (
    "why_it_matters", "what_is_known", "what_remains_unknown", "rationale",
    "testable_prediction", "proposed_test", "evidence",
)


# ----------------------------------------------------------------------------
# Generic helpers
# ----------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc).isoformat()


def _text(content):
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


def _as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _count(parsed, key):
    value = parsed.get(key, []) if isinstance(parsed, dict) else []
    return len(value) if isinstance(value, list) else 0


# ----------------------------------------------------------------------------
# LangChain structured-output schemas
# ----------------------------------------------------------------------------

def _structured_schema(stage):
    """JSON Schema contracts for Gemini's native structured-output mode."""
    def obj(properties):
        return {"type": "object", "properties": properties,
                "required": list(properties), "additionalProperties": False}

    def arr(item):
        return {"type": "array", "items": item}

    string = {"type": "string"}
    strings = arr(string)
    paper_ref = obj({"paper_id": string, "sections": strings})
    related_paper = obj({"paper_id": string, "sections": strings,
                         "relation": string, "explanation": string})
    evidence = obj({"paper_id": string, "section": string, "evidence": string})
    open_question = obj({"question": string, "why_unresolved": string,
                         "evidence": string, "sections": strings})
    candidate_hypothesis = obj({"hypothesis": string, "rationale": string,
                                "evidence": string, "sections": strings})

    reader = obj({
        "paper_title": string, "authors_year": string,
        "research_question": string, "context": string,
        "methods": strings, "main_findings": strings, "assumptions": strings,
        "limitations_explicit": strings,
        "potential_open_questions": arr(open_question),
        "candidate_hypotheses": arr(candidate_hypothesis),
    })
    gap = obj({
        "id": string, "gap": string, "why_it_matters": string,
        "what_is_known": string, "what_remains_unknown": string,
        "gap_type": string, "confidence": string,
        "supporting_papers": arr(paper_ref),
        "related_papers": arr(related_paper), "evidence": arr(evidence),
    })
    hypothesis = obj({
        "id": string, "hypothesis": string, "rationale": string,
        "testable_prediction": string, "proposed_test": string,
        "originating_gap_ids": strings,
        "supporting_papers": arr(paper_ref),
        "related_papers": arr(related_paper), "evidence": arr(evidence),
    })
    critique_change = obj({
        "target_id": string, "action": string, "category": string,
        "argument": string, "evidence": arr(evidence),
        "paper_references": arr(paper_ref), "proposed_revision": string,
        "merge_with": strings,
    })
    revised_record = obj({
        "id": string, "gap_or_hypothesis_text": string,
        "why_it_matters": string, "what_is_known": string,
        "what_remains_unknown": string, "rationale": string,
        "testable_prediction": string, "proposed_test": string,
        "supporting_papers": arr(paper_ref),
        "related_papers": arr(related_paper), "evidence": arr(evidence),
    })
    decision = obj({
        "target_id": string, "decision": string, "reason": string,
        "merged_ids": strings, "revised_record": revised_record,
        "remaining_uncertainties": strings,
    })

    schemas = {
        "paper_analysis": reader,
        "research_gap_generation": obj({
            "historical_analysis": string, "research_gaps": arr(gap),
        }),
        "hypothesis_generation": obj({"hypotheses": arr(hypothesis)}),
        "self_critique": obj({
            "proposed_changes": arr(critique_change), "no_change_reason": string,
        }),
        "self_critique_revision": obj({
            "decisions": arr(decision), "round_summary": string,
        }),
    }
    if stage not in schemas:
        raise ValueError(f"No structured-output schema defined for stage: {stage}")
    return schemas[stage]


# ----------------------------------------------------------------------------
# API runner: throttling, retries, usage and inference-history logging
# ----------------------------------------------------------------------------

class _Runner:
    def __init__(self, llm, model_name, prices, pause_sec, max_retries):
        self.llm = llm
        self.model_name = model_name
        self.prices = prices or {}
        self.pause_sec = pause_sec
        self.max_retries = max_retries
        self.history = []
        self.usage = []
        self.last_failure = None  # ("request" | "parse", message) after a failed call
        self._last_done = None

    def note(self, stage, status, message, **extra):
        """Log an orchestrator event (no API call)."""
        event = {
            "event_id": f"E{len(self.history)+1:04d}", "timestamp_utc": _now(),
            "stage": stage, "agent": "Orchestrator", "status": status, "message": message,
        }
        event.update(extra)
        self.history.append(event)

    def _wait(self):
        if self._last_done is None:
            return
        delay = self.pause_sec - (time.monotonic() - self._last_done)
        if delay > 0:
            print(f"[WAIT] {delay:.1f}s before next API call")
            time.sleep(delay)

    def _report(self, stage, paper_loc, round_no, parsed=None, runtime=None, error=None):
        label = _LABELS.get(stage, stage.upper())
        if round_no is not None:
            label += f" R{round_no}"
        subject = Path(paper_loc).name if paper_loc else "Single Researcher"
        if error:
            detail = f"FAILED — {error}"
        elif parsed is None:
            detail = "FAILED — invalid JSON response"
        elif stage == "research_gap_generation":
            detail = f"Generated {_count(parsed, 'research_gaps')} research gaps"
        elif stage == "hypothesis_generation":
            detail = f"Generated {_count(parsed, 'hypotheses')} hypotheses"
        elif stage == "self_critique":
            detail = f"Proposed {_count(parsed, 'proposed_changes')} changes"
        elif stage == "self_critique_revision":
            detail = f"Decided on {_count(parsed, 'decisions')} records"
        else:
            detail = "Completed"
        timing = f" ({runtime:.1f}s)" if runtime is not None else ""
        print(f"[SINGLE] {label} — {subject}: {detail}{timing}")

    def call(self, prompt, *, stage, agent="Single Researcher", paper_path=None, round_no=None):
        """One LLM request. Returns the parsed JSON dict, or None on failure."""
        self.last_failure = None
        paper_loc = str(Path(paper_path).resolve()) if paper_path else None
        event = {
            "event_id": f"E{len(self.history)+1:04d}", "timestamp_utc": _now(),
            "stage": stage, "agent": agent, "round": round_no, "paper_loc": paper_loc,
            "prompt": prompt, "status": "started",
        }
        self.history.append(event)
        try:
            if paper_path:
                encoded_pdf = base64.b64encode(Path(paper_path).resolve().read_bytes()).decode("ascii")
                message = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
                ])
            else:
                message = HumanMessage(content=prompt)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            event.update(status="error", error=error)
            self.last_failure = ("request", error)
            self._report(stage, paper_loc, round_no, error=error)
            return None

        for attempt in range(1, self.max_retries + 1):
            self._wait()
            started = time.perf_counter()
            try:
                structured_llm = self.llm.with_structured_output(
                    _structured_schema(stage),
                    method="json_schema",
                    include_raw=True,
                )
                structured_result = structured_llm.invoke([message])
            except Exception as exc:
                runtime = round(time.perf_counter() - started, 3)
                self._last_done = time.monotonic()
                error = f"{type(exc).__name__}: {exc}"
                self.usage.append({
                    "timestamp_utc": _now(), "stage": stage, "agent": agent,
                    "round": round_no, "paper_loc": paper_loc, "model": self.model_name,
                    "attempt": attempt, "status": "error", "runtime_seconds": runtime,
                    "input_tokens": None, "output_tokens": None, "total_tokens": None,
                    "estimated_cost_usd": None, "error": error,
                })
                if any(term in str(exc).lower() for term in _RETRYABLE_TERMS) and attempt < self.max_retries:
                    backoff = self.pause_sec * (2 ** (attempt - 1))
                    print(f"[WAIT] {backoff:.1f}s before retrying {stage}")
                    time.sleep(backoff)
                    self._last_done = time.monotonic()
                    continue
                event.update(status="error", error=error, runtime_seconds=runtime, attempts=attempt)
                self.last_failure = ("request", error)
                self._report(stage, paper_loc, round_no, error=error)
                return None

            runtime = round(time.perf_counter() - started, 3)
            self._last_done = time.monotonic()
            response = structured_result.get("raw")
            parsed = structured_result.get("parsed")
            parsing_error = structured_result.get("parsing_error")
            if hasattr(parsed, "model_dump"):
                parsed = parsed.model_dump()
            if not isinstance(parsed, dict):
                parsed = None

            meta = getattr(response, "usage_metadata", None) or {}
            inp, out, total = meta.get("input_tokens"), meta.get("output_tokens"), meta.get("total_tokens")
            if total is None and inp is not None and out is not None:
                total = inp + out
            cost = None
            if (inp is not None and out is not None and self.prices.get("input") is not None
                    and self.prices.get("output") is not None):
                cost = (inp * self.prices["input"] + out * self.prices["output"]) / 1_000_000
            self.usage.append({
                "timestamp_utc": _now(), "stage": stage, "agent": agent,
                "round": round_no, "paper_loc": paper_loc, "model": self.model_name,
                "attempt": attempt, "status": "success" if parsed is not None else "parse_error",
                "runtime_seconds": runtime, "input_tokens": inp, "output_tokens": out,
                "total_tokens": total, "estimated_cost_usd": cost,
                "error": str(parsing_error) if parsing_error else None,
            })
            raw = _text(response.content) if response is not None else ""
            event.update(
                status="success" if parsed is not None else "parse_error",
                response=raw, parsed_output=parsed,
                structured_output_error=str(parsing_error) if parsing_error else None,
                runtime_seconds=runtime, attempts=attempt,
            )
            if parsed is None:
                message = ("LangChain structured output did not produce a parsed object: "
                           + (str(parsing_error) if parsing_error else "unknown parsing error"))
                event["parse_warning"] = message
                self.last_failure = ("parse", message)
            self._report(stage, paper_loc, round_no, parsed, runtime)
            return parsed
        return None


# ----------------------------------------------------------------------------
# Paper cards and reference/evidence helpers
# ----------------------------------------------------------------------------

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


def _merge_refs(*groups):
    return _normal_refs(
        [ref for group in groups for ref in (group or [])],
        {ref.get("paper_id") for group in groups for ref in (group or [])
         if isinstance(ref, dict) and ref.get("paper_id")}
    )


def _merge_evidence(*groups):
    merged, seen = [], set()
    for group in groups:
        for item in _as_list(group):
            key = json.dumps(item, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                merged.append(item)
    return merged


# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------

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


def _gap_generation_prompt(topic, additional, cards, existing_gaps, target_count, batch_size, iteration):
    return f"""
You are a single scientific researcher conducting an ITERATIVE literature-gap search.
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
SEARCH ITERATION: {iteration}
TARGET TOTAL: approximately {target_count} distinct research gaps.
GENERATE THIS ITERATION: at most {batch_size} NEW gaps.

Use ONLY the supplied paper summaries as evidence. Do not imply that this corpus
represents all published literature. Distinguish explicit findings, reasonable
inferences, and speculation.

Search the corpus systematically for additional, distinct unresolved research
questions. Examine methods, assumptions, datasets, evaluation choices, theoretical
claims, limitations, conflicting findings, and underexplored connections. In each
iteration, prioritize areas not already represented by the existing gaps. Do not
paraphrase, split, or lightly reword an existing gap to inflate the count.
The target is approximate, not a quota: return fewer gaps if the corpus does not
support more substantive gaps. If no meaningful new gap remains, return an empty list.

Each gap must explain what is known, what remains unknown and why it matters.
Cite direct evidence and supporting papers using only supplied paper IDs. Use
section references where possible; sections may be empty but paper IDs must be valid.
A limitation or a paper's silence is not automatically a research gap.

Return ONLY valid JSON, no Markdown:
{{"historical_analysis":"",
"research_gaps":[{{"id":"","gap":"","why_it_matters":"","what_is_known":"",
"what_remains_unknown":"","gap_type":"explicit|inferred","confidence":"low|medium|high",
"supporting_papers":[{{"paper_id":"P001","sections":[]}}],
"related_papers":[{{"paper_id":"P001","sections":[],"relation":"addresses|contradicts|extends|mentions","explanation":""}}],
"evidence":[{{"paper_id":"P001","section":"","evidence":""}}]}}]}}

EXISTING GAPS — DO NOT DUPLICATE:
{_dump(existing_gaps)}
PAPER SUMMARIES:
{_dump(cards)}
"""


def _hypothesis_generation_prompt(topic, additional, gaps, cards):
    return f"""
You are a single scientific researcher generating hypotheses from the completed
research-gap list.
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}

Generate specific, falsifiable hypotheses grounded in the supplied final gaps.
Aim for approximately one substantive hypothesis per gap where justified, so the
number of hypotheses is broadly comparable to the number of gaps. Do not force a
hypothesis for a gap if the evidence does not support a testable proposition.
Each hypothesis must cite one or more valid originating gap IDs and supporting
paper IDs/sections, and include a rationale, testable prediction and proposed test.
Avoid duplicate or overlapping hypotheses. Do not claim proof or novelty beyond
the supplied corpus.

Return ONLY valid JSON, no Markdown:
{{"hypotheses":[{{"id":"","hypothesis":"","rationale":"","testable_prediction":"",
"proposed_test":"","originating_gap_ids":["G001"],
"supporting_papers":[{{"paper_id":"P001","sections":[]}}],
"related_papers":[{{"paper_id":"P001","sections":[],"relation":"addresses|contradicts|extends|mentions","explanation":""}}],
"evidence":[{{"paper_id":"P001","section":"","evidence":""}}]}}]}}

FINAL RESEARCH GAPS:
{_dump(gaps)}
PAPER SUMMARIES:
{_dump(cards)}
"""


def _critique_prompt(topic, additional, rnd, max_rounds, records, cards):
    return f"""
You are the SAME single researcher who produced the records below.
Perform ONE self-critique (round {rnd}/{max_rounds}) of EVERY record, gaps and
hypotheses alike. Do not simulate other agents, personas, reviewers, or a debate.
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
It is not mandatory to propose changes. Only suggest changes when necessary; do not
manufacture problems. Categories: unsupported_by_cited_papers, already_addressed,
infeasible, vague, non_falsifiable. Treat a gap that rests only on a paper's silence as
unsupported_by_cited_papers, and duplicate or overlapping records as a merge. Cite
corpus paper IDs and sections. Corpus-only, no web search or outside knowledge.
Return only JSON:
{{"proposed_changes":[{{"target_id":"","action":"revise|reject|merge|retain",
"category":"unsupported_by_cited_papers|already_addressed|infeasible|vague|non_falsifiable",
"argument":"","evidence":[],"paper_references":[],
"proposed_revision":"","merge_with":[]}}],"no_change_reason":""}}
RECORDS: {_dump(records)}
PAPER SUMMARIES: {_dump(cards)}
"""


def _revision_prompt(topic, additional, rnd, max_rounds, records, changes, cards):
    return f"""
You are the SAME single researcher who produced the records and wrote the critique below.
Perform ONE revision (round {rnd}/{max_rounds}). Do not simulate other agents,
personas, reviewers, or a debate, and do not critique the revised version again.
TOPIC: {topic}
USER INSTRUCTIONS: {additional or "None"}
For every critique, accept it (revise, merge or reject the record) or decline it
(retain). Do not accept merely to comply and do not decline merely to keep the draft.
For a revision, rewrite the COMPLETE record including supporting_papers, related_papers
and evidence. Never change or renumber IDs. A merge keeps one existing ID and lists
absorbed IDs. Do not silently drop records. Preserve uncertainties. Cite corpus paper IDs
and sections.
Return only JSON:
{{"decisions":[{{"target_id":"","decision":"retain|revise|merge|reject",
"reason":"","merged_ids":[],"revised_record":{{"id":"",
"gap_or_hypothesis_text":"","why_it_matters":"","what_is_known":"",
"what_remains_unknown":"","rationale":"","testable_prediction":"",
"proposed_test":"","supporting_papers":[],"related_papers":[],"evidence":[]}},
"remaining_uncertainties":[]}}],"round_summary":""}}
RECORDS: {_dump(records)}
CRITIQUE: {_dump(changes)}
PAPER SUMMARIES: {_dump(cards)}
"""


# ----------------------------------------------------------------------------
# Records: creation, revision, merging, and gap/hypothesis link bookkeeping
# ----------------------------------------------------------------------------

def _new_record(raw, rid, valid_ids):
    item = dict(raw)
    item.update({
        "id": rid, "origin_perspective": None, "origin_perspectives": [],
        "status": "candidate",
        "supporting_papers": _normal_refs(item.get("supporting_papers"), valid_ids),
        "related_papers": _normal_related(item.get("related_papers"), valid_ids),
        "debate_history": [],
    })
    item["evidence"] = _as_list(item.get("evidence"))
    return item


def _draft_records(parsed, valid_ids):
    """Number the draft's gaps/hypotheses and validate paper and gap references."""
    gaps, hypotheses, id_map = [], [], {}
    raw_gaps = parsed.get("research_gaps")
    for raw in raw_gaps if isinstance(raw_gaps, list) else []:
        if not isinstance(raw, dict) or not raw.get("gap"):
            continue
        rid = f"G{len(gaps)+1:03d}"
        if raw.get("id"):
            id_map[str(raw["id"])] = rid
        gaps.append(_new_record(raw, rid, valid_ids))
    known = {g["id"] for g in gaps}
    raw_hyps = parsed.get("hypotheses")
    for raw in raw_hyps if isinstance(raw_hyps, list) else []:
        if not isinstance(raw, dict) or not raw.get("hypothesis"):
            continue
        record = _new_record(raw, f"H{len(hypotheses)+1:03d}", valid_ids)
        linked = []
        for gid in _as_list(raw.get("originating_gap_ids")):
            gid = id_map.get(str(gid), str(gid))
            if gid in known and gid not in linked:
                linked.append(gid)
        record["originating_gap_ids"] = linked
        hypotheses.append(record)
    return gaps, hypotheses


def _active(records):
    return [x for x in records if x.get("status") not in ("rejected", "merged")]


def _apply_revision(rec, revised, key, valid_ids):
    """Apply a revised_record to rec. Empty values never wipe existing content."""
    if not isinstance(revised, dict):
        return False
    new_text = revised.get("gap_or_hypothesis_text") or revised.get(key)
    if new_text:
        rec.setdefault("previous_versions", []).append(rec.get(key))
        rec[key] = new_text
    for field in _REVISION_FIELDS:
        value = revised.get(field)
        if value not in (None, "", []):
            rec[field] = value
    rec["supporting_papers"] = _merge_refs(
        rec.get("supporting_papers"),
        _normal_refs(revised.get("supporting_papers"), valid_ids))
    rec["related_papers"] = rec.get("related_papers", []) + _normal_related(
        revised.get("related_papers"), valid_ids)
    return True


def _apply_decisions(records, decisions, changes, rnd, valid_ids):
    """Apply the reviser's decisions to the active records (mutates them in place)."""
    by_id = {x["id"]: x for x in records}
    for decision in decisions if isinstance(decisions, list) else []:
        if not isinstance(decision, dict):
            continue
        rid = decision.get("target_id")
        rec = by_id.get(rid)
        if not rec or rec.get("status") in ("rejected", "merged"):
            continue
        key = "gap" if rid.startswith("G") else "hypothesis"
        decision["round"] = rnd
        rec.setdefault("debate_history", []).append({
            "round": rnd,
            "challenge": [x for x in changes if x.get("target_id") == rid],
            "defence": [],
            "decision": decision,
        })
        rec["last_decision"] = decision
        action = decision.get("decision", "retain")
        if action == "reject":
            rec.update(status="rejected", rejection_reason=decision.get("reason", ""))
        elif action in ("merge", "revise"):
            if action == "merge":
                absorbed_ids = [
                    str(m) for m in _as_list(decision.get("merged_ids"))
                    if str(m) in by_id and str(m) != rid and str(m)[0] == rid[0]
                    and by_id[str(m)].get("status") not in ("rejected", "merged")
                ]
                rec["merged_ids"] = list(dict.fromkeys(rec.get("merged_ids", []) + absorbed_ids))
                for mid in absorbed_ids:
                    absorbed = by_id[mid]
                    rec["supporting_papers"] = _merge_refs(
                        rec.get("supporting_papers"), absorbed.get("supporting_papers"))
                    rec["related_papers"] = rec.get("related_papers", []) + absorbed.get("related_papers", [])
                    rec["evidence"] = _merge_evidence(rec.get("evidence"), absorbed.get("evidence"))
                    absorbed.update(status="merged", merged_into=rid,
                                    merge_reason=decision.get("reason", ""))
                    absorbed.setdefault("debate_history", []).append({
                        "round": rnd, "challenge": [], "defence": [],
                        "decision": {"decision": "absorbed", "merged_into": rid,
                                     "reason": decision.get("reason", ""), "round": rnd},
                    })
            changed = _apply_revision(rec, decision.get("revised_record"), key, valid_ids)
            rec["status"] = "revised" if (action == "revise" or changed) else "retained"
        else:
            rec["status"] = "retained"


def _sync_gap_links(gaps, hypotheses, runner, rnd):
    """Point hypotheses at surviving gaps after merges/rejections; warn about orphans."""
    alive = {g["id"] for g in _active(gaps)}
    merged_into = {g["id"]: g.get("merged_into") for g in gaps if g.get("status") == "merged"}
    for h in _active(hypotheses):
        linked = []
        for gid in h.get("originating_gap_ids", []):
            hops = 0
            while gid in merged_into and hops < 20:
                gid, hops = merged_into[gid], hops + 1
            if gid in alive and gid not in linked:
                linked.append(gid)
        if h.get("originating_gap_ids") and not linked:
            runner.note("orphaned_hypothesis_warning", "warning",
                        f"{h['id']} has no surviving originating gap after round {rnd}; retained.",
                        round=rnd)
        h["originating_gap_ids"] = linked


def _format_gap(item):
    refs = []
    for ref in item.get("supporting_papers", []):
        section = ", ".join(ref.get("sections", []))
        refs.append(ref["paper_id"] + (f" ({section})" if section else ""))
    suffix = " [Papers: " + "; ".join(refs) + "]" if refs else ""
    return f"{item.get('id')}: {item.get('gap', '')}{suffix}"


def _history_text(topic, events):
    lines = ["=" * 80, "ATR SINGLE-AGENT INFERENCE HISTORY", f"Topic: {topic}",
             f"Generated: {_now()}", "=" * 80, ""]
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


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------

def run_single_agent(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None, *, max_rounds, pause_sec, max_retries,
                     target_gap_count=10):
    """Run the single-agent pipeline and return results/logs to main.py."""
    if not isinstance(target_gap_count, int) or target_gap_count < 1:
        raise ValueError("target_gap_count must be an integer >= 1.")
    runner = _Runner(llm, model_name, price_per_million_tokens, pause_sec, max_retries)
    total_start = time.perf_counter()
    pdf_paths = [Path(path).resolve() for path in pdf_paths]
    papers = []

    # Stage 1: each paper is read in its own sequential request.
    print(f"[SINGLE] Reading {len(pdf_paths)} papers sequentially.")
    for index, pdf_path in enumerate(pdf_paths, start=1):
        pid = f"P{index:03d}"
        parsed = runner.call(
            _reader_prompt(topic, additional_prompt, pid, pdf_path),
            stage="paper_analysis", paper_path=pdf_path)
        if not isinstance(parsed, dict):
            runner.note("paper_analysis_skipped", "warning",
                        "No analysis generated for this paper.",
                        paper_id=pid, paper_loc=str(pdf_path))
            continue
        papers.append({"paper_id": pid, "paper_loc": str(pdf_path),
                       "paper_filename": pdf_path.name, "analysis": parsed})
        runner.note("paper_analysis_log", "success", f"Analysed: {pdf_path.name}",
                    paper_id=pid, paper_loc=str(pdf_path))

    gaps, hypotheses = [], []
    historical_analysis = ""
    draft_records = {"research_gaps": [], "hypotheses": []}
    rounds, round_summaries = [], []
    executed, terminated_early = 0, False
    parse_warning = synthesis_warning = critique_warning = analysis_warning = None

    if not papers:
        analysis_warning = "No papers were successfully analysed."
    else:
        cards = _paper_cards(papers)
        valid_ids = {c["paper_id"] for c in cards}

        # Stage 2: iterative gap search. Each call explores areas not covered by
        # earlier gaps; stop at the target or when the model finds no further gaps.
        raw_gaps = []
        iteration = 0
        batch_size = min(3, target_gap_count)
        while len(raw_gaps) < target_gap_count:
            iteration += 1
            existing = [
                {"id": f"G{i:03d}", **{k: v for k, v in item.items() if k != "id"}}
                for i, item in enumerate(raw_gaps, start=1)
            ]
            parsed = runner.call(
                _gap_generation_prompt(
                    topic, additional_prompt, cards, existing, target_gap_count,
                    min(batch_size, target_gap_count - len(raw_gaps)), iteration),
                stage="research_gap_generation", round_no=iteration)
            if parsed is None:
                kind, message = runner.last_failure or ("request", "unknown failure")
                if kind == "parse":
                    parse_warning = message
                synthesis_warning = (
                    f"Gap-generation iteration {iteration} failed; retained gaps "
                    "from earlier iterations.")
                break

            if not historical_analysis:
                historical_analysis = parsed.get("historical_analysis", "")
            new_items = parsed.get("research_gaps", [])
            new_items = [
                item for item in new_items
                if isinstance(item, dict) and item.get("gap")
            ] if isinstance(new_items, list) else []
            if not new_items:
                runner.note(
                    "gap_generation_terminated", "success",
                    "No additional substantive gaps returned; iterative search stopped.",
                    iteration=iteration, gaps_found=len(raw_gaps))
                break

            # Assign stable sequential IDs locally; ignore model-provided IDs.
            # Also guard against repeated gaps across iterations.
            existing_texts = {
                " ".join(str(item.get("gap", "")).lower().split())
                for item in raw_gaps
            }
            added_this_iteration = 0
            for item in new_items:
                if len(raw_gaps) >= target_gap_count:
                    break
                item = dict(item)
                normalized = " ".join(str(item.get("gap", "")).lower().split())
                if not normalized or normalized in existing_texts:
                    continue
                item["id"] = f"G{len(raw_gaps) + 1:03d}"
                raw_gaps.append(item)
                existing_texts.add(normalized)
                added_this_iteration += 1

            if added_this_iteration == 0:
                runner.note(
                    "gap_generation_terminated", "warning",
                    "Iteration produced no new distinct gaps; iterative search stopped.",
                    iteration=iteration, gaps_found=len(raw_gaps))
                break

        # Stage 3: generate hypotheses only after the complete gap list exists.
        gap_draft = {"research_gaps": raw_gaps, "hypotheses": []}
        gaps, _ = _draft_records(gap_draft, valid_ids)
        raw_hypotheses = []
        if gaps:
            hypothesis_draft = runner.call(
                _hypothesis_generation_prompt(
                    topic, additional_prompt, gaps, cards),
                stage="hypothesis_generation")
            if hypothesis_draft is None:
                synthesis_warning = synthesis_warning or (
                    "Hypothesis-generation request failed or returned invalid JSON.")
            else:
                raw_hypotheses = hypothesis_draft.get("hypotheses", [])
                if not isinstance(raw_hypotheses, list):
                    raw_hypotheses = []
        gaps, hypotheses = _draft_records(
            {"research_gaps": raw_gaps, "hypotheses": raw_hypotheses}, valid_ids)
        if not gaps and not hypotheses:
            synthesis_warning = synthesis_warning or (
                "Iterative search returned no usable gap or hypothesis records.")
        draft_records = copy.deepcopy({"research_gaps": gaps, "hypotheses": hypotheses})

        # Stage 3: self-critique -> revision rounds by the same researcher.
        for rnd in range(1, max_rounds + 1):
            records = _active(gaps) + _active(hypotheses)
            if not records:
                break
            critique = runner.call(
                _critique_prompt(topic, additional_prompt, rnd, max_rounds, records, cards),
                stage="self_critique", round_no=rnd)
            if critique is None:
                critique_warning = (f"Round {rnd}: critique request failed or returned invalid "
                                    "JSON; kept the previous records.")
                break
            executed += 1
            raw_changes = critique.get("proposed_changes", [])
            changes = [c for c in raw_changes if isinstance(c, dict)] if isinstance(raw_changes, list) else []
            if not changes:
                runner.note("self_critique_terminated", "success",
                            "No critique changes; revision and later rounds skipped.", round=rnd)
                rounds.append({
                    "round": rnd, "critiques": [], "decisions": [], "terminated": True,
                    "reason": critique.get("no_change_reason", ""),
                    "records_after": copy.deepcopy({"research_gaps": _active(gaps),
                                                    "hypotheses": _active(hypotheses)}),
                })
                terminated_early = True
                break

            revision = runner.call(
                _revision_prompt(topic, additional_prompt, rnd, max_rounds, records, changes, cards),
                stage="self_critique_revision", round_no=rnd)
            if revision is None:
                critique_warning = (f"Round {rnd}: revision request failed or returned invalid "
                                    "JSON; kept the previous records.")
                rounds.append({"round": rnd, "critiques": changes, "decisions": [],
                               "terminated": False, "failed": True})
                break
            decisions = revision.get("decisions", [])
            _apply_decisions(records, decisions, changes, rnd, valid_ids)
            _sync_gap_links(gaps, hypotheses, runner, rnd)
            summary = revision.get("round_summary", "")
            round_summaries.append(summary)
            rounds.append({
                "round": rnd, "critiques": changes,
                "decisions": decisions if isinstance(decisions, list) else [],
                "round_summary": summary, "terminated": False,
                "records_after": copy.deepcopy({"research_gaps": _active(gaps),
                                                "hypotheses": _active(hypotheses)}),
            })

    for rec in gaps + hypotheses:
        if rec.get("status") == "candidate":
            rec["status"] = "accepted"
    final_gaps, final_hypotheses = _active(gaps), _active(hypotheses)
    rejected_gaps = [x for x in gaps if x.get("status") == "rejected"]
    rejected_hypotheses = [x for x in hypotheses if x.get("status") == "rejected"]
    merged_or_rejected = [
        {"id": x["id"], "decision": x["status"],
         "reason": x.get("rejection_reason") or x.get("merge_reason", ""),
         "merged_ids": x.get("merged_ids", []),
         "merged_into": x.get("merged_into"),
         "merge_reason": x.get("merge_reason", ""),
         "gap": x.get("gap", ""),
         "hypothesis": x.get("hypothesis", ""),
         "gap_or_hypothesis_text": x.get("gap") or x.get("hypothesis", ""),
         "why_it_matters": x.get("why_it_matters", ""),
         "rationale": x.get("rationale", ""),
         "supporting_papers": x.get("supporting_papers", []),
         "related_papers": x.get("related_papers", []),
         "evidence": x.get("evidence", []),
         "revised_record": x.get("last_decision", {}).get("revised_record", {})}
        for x in gaps + hypotheses if x.get("status") in ("rejected", "merged")
    ]

    successful = [x for x in runner.usage if x["status"] == "success"]
    costs = [x["estimated_cost_usd"] for x in successful if x["estimated_cost_usd"] is not None]
    usage_summary = {
        "api_calls_logged": len(runner.usage),
        "successful_calls": len(successful),
        "failed_calls": len(runner.usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - total_start, 3),
    }

    runner.note("final_result", "success",
                f"{len(final_gaps)} gaps and {len(final_hypotheses)} hypotheses.")
    return {
        "agent_params": {
            "mode": "single", "topic": topic, "additional_prompt": additional_prompt,
            "model": model_name,
            "papers": [{"paper_id": p["paper_id"], "paper_loc": p["paper_loc"]} for p in papers],
            "perspectives": [], "debate_rounds_max": 0,
            "debate_termination": ("Not applicable; self-critique and revision rounds stop "
                                   "when the critique proposes no changes."),
            "execution": "Sequential API calls; no concurrent requests.",
            "pause_after_response_seconds": pause_sec, "max_retries": max_retries,
            "web_search": False,
            "self_critique_rounds": max_rounds, "refinement_rounds": max_rounds,
            "self_critique_rounds_executed": executed,
            "target_gap_count": target_gap_count,
            "gap_generation_strategy": "Iterative batches; stop at target or when no new substantive gaps are returned.",
        },
        "paper_analyses": papers, "perspective_finder_output": None,
        "historical_analysis": historical_analysis,
        "research_gaps": [_format_gap(x) for x in final_gaps],
        "research_gap_records": final_gaps,
        "hypotheses": final_hypotheses,
        "rejected_research_gaps": rejected_gaps,
        "rejected_hypotheses": rejected_hypotheses,
        "debate_summaries": {"research_gaps": [], "hypotheses": []},
        "draft_records": draft_records,
        "critique_rounds": rounds,
        "curation": {"initial": None, "final_summary": "\n".join(s for s in round_summaries if s),
                     "merged_or_rejected": merged_or_rejected},
        "self_critique": {"rounds_executed": executed, "max_rounds": max_rounds,
                          "terminated_early": terminated_early,
                          "round_summaries": round_summaries},
        "parse_warning": parse_warning,
        "synthesis_warning": synthesis_warning,
        "critique_warning": critique_warning,
        "analysis_warning": analysis_warning,
        "usage_summary": usage_summary, "api_usage": runner.usage,
        "inference_history": runner.history,
        "inference_history_text": _history_text(topic, runner.history),
    }
