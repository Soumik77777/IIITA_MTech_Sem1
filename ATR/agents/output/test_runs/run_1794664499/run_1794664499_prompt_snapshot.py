"""ATR adaptive multi-agent research-gap and hypothesis pipeline.

Run controls (max_rounds = debate rounds per subject, pause_sec, max_retries) are passed in
by main.py, so they are not part of this module's architecture snapshot.
"""
import base64
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

EXAMPLE_PERSPECTIVES = {
    "theoretical": "Explanations, assumptions, mathematical consistency, guarantees and predictions.",
    "computational": "Algorithms, numerical methods, simulations, complexity and reproducibility.",
    "observational": "Measurements, data limitations, parameter degeneracies and model-observation mismatch.",
    "experimental": "Testability and controlled laboratory, physical, numerical or code-based experiments.",
}
_RETRYABLE_TERMS = (
    "429", "resource_exhausted", "rate limit", "too many requests",
    "503", "service unavailable", "502", "504",
)
_REVISION_FIELDS = (
    "why_it_matters", "what_is_known", "what_remains_unknown", "rationale",
    "testable_prediction", "proposed_test", "evidence",
)


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


def _print_call_result(stage, agent, parsed, paper_loc=None, runtime=None, error=None):
    role = {
        "paper_reading": "READER", "perspective_discovery": "PERSPECTIVE FINDER",
        "research_gap_generation": "GAPS GENERATOR",
        "initial_gap_curation_and_corpus_analysis": "CURATOR",
        "research_gap_challenger": "CHALLENGER",
        "research_gap_defender": "DEFENDER",
        "research_gap_adjudication": "ADJUDICATOR",
        "hypothesis_generation": "HYPOTHESES GENERATOR",
        "hypothesis_challenger": "CHALLENGER",
        "hypothesis_defender": "DEFENDER",
        "hypothesis_adjudication": "ADJUDICATOR",
        "final_curation": "FINAL CURATOR",
    }.get(stage, agent.upper())
    if error:
        detail = f"FAILED — {error}"
    elif parsed is None:
        detail = "FAILED — invalid JSON response"
    else:
        count = None
        if stage == "research_gap_generation":
            count = len(parsed.get("research_gaps", [])) if isinstance(parsed, dict) and isinstance(parsed.get("research_gaps", []), list) else 0
            detail = f"Generated {count} gaps"
        elif stage == "hypothesis_generation":
            count = len(parsed.get("hypotheses", [])) if isinstance(parsed, dict) and isinstance(parsed.get("hypotheses", []), list) else 0
            detail = f"Generated {count} hypotheses"
        elif stage == "perspective_discovery":
            count = len(parsed.get("perspectives", [])) if isinstance(parsed, dict) and isinstance(parsed.get("perspectives", []), list) else 0
            detail = f"Generated {count} perspectives"
        elif stage.endswith("_challenger"):
            count = len(parsed.get("proposed_changes", [])) if isinstance(parsed, dict) and isinstance(parsed.get("proposed_changes", []), list) else 0
            detail = f"Challenged {count} proposals"
        elif stage.endswith("_defender"):
            count = len(parsed.get("responses", [])) if isinstance(parsed, dict) and isinstance(parsed.get("responses", []), list) else 0
            detail = f"Defended {count} proposals"
        elif stage.endswith("_adjudication"):
            count = len(parsed.get("decisions", [])) if isinstance(parsed, dict) and isinstance(parsed.get("decisions", []), list) else 0
            detail = f"Adjudicated {count} proposals"
        elif stage == "paper_reading":
            detail = "Analysed paper"
        elif stage == "final_curation":
            detail = "Final curation completed"
        else:
            detail = "Completed"
    subject = Path(paper_loc).name if paper_loc else agent
    timing = f" ({runtime:.1f}s)" if runtime is not None else ""
    print(f"[{role}] {subject}: {detail}{timing}")




def _structured_schema(stage):
    """JSON Schema contracts passed to Gemini's native structured-output mode."""
    record = {
        "type": "object",
        "properties": {'id': {'type': 'string'}, 'paper_id': {'type': 'string'}, 'paper_title': {'type': 'string'}, 'authors_year': {'type': 'string'}, 'research_question': {'type': 'string'}, 'context': {'type': 'string'}, 'methods': {'type': 'array', 'items': {'type': 'string'}}, 'main_findings': {'type': 'array', 'items': {'type': 'string'}}, 'assumptions': {'type': 'array', 'items': {'type': 'string'}}, 'limitations_explicit': {'type': 'array', 'items': {'type': 'string'}}, 'potential_open_questions': {'type': 'array', 'items': {'type': 'object', 'properties': {'question': {'type': 'string'}, 'why_unresolved': {'type': 'string'}, 'evidence': {'type': 'string'}, 'sections': {'type': 'array', 'items': {'type': 'string'}}}, 'required': [], 'additionalProperties': False}}, 'candidate_hypotheses': {'type': 'array', 'items': {'type': 'object', 'properties': {'hypothesis': {'type': 'string'}, 'rationale': {'type': 'string'}, 'evidence': {'type': 'string'}, 'sections': {'type': 'array', 'items': {'type': 'string'}}}, 'required': [], 'additionalProperties': False}}, 'gap': {'type': 'string'}, 'hypothesis': {'type': 'string'}, 'why_it_matters': {'type': 'string'}, 'what_is_known': {'type': 'string'}, 'what_remains_unknown': {'type': 'string'}, 'gap_type': {'type': 'string'}, 'confidence': {'type': 'string'}, 'rationale': {'type': 'string'}, 'testable_prediction': {'type': 'string'}, 'proposed_test': {'type': 'string'}, 'decision': {'type': 'string'}, 'reason': {'type': 'string'}, 'merged_ids': {'type': 'array', 'items': {'type': 'string'}}, 'origin_perspectives': {'type': 'array', 'items': {'type': 'string'}}, 'originating_gap_ids': {'type': 'array', 'items': {'type': 'string'}}, 'sections': {'type': 'array', 'items': {'type': 'string'}}, 'supporting_papers': {'type': 'array', 'items': {'type': 'object', 'properties': {'paper_id': {'type': 'string'}, 'sections': {'type': 'array', 'items': {'type': 'string'}}}, 'required': [], 'additionalProperties': False}}, 'related_papers': {'type': 'array', 'items': {'type': 'object', 'properties': {'paper_id': {'type': 'string'}, 'sections': {'type': 'array', 'items': {'type': 'string'}}, 'relation': {'type': 'string'}, 'explanation': {'type': 'string'}}, 'required': [], 'additionalProperties': False}}, 'evidence': {'type': 'array', 'items': {'type': 'object', 'properties': {'paper_id': {'type': 'string'}, 'section': {'type': 'string'}, 'evidence': {'type': 'string'}}, 'required': [], 'additionalProperties': False}}, 'status': {'type': 'string'}, 'merged_into': {'type': 'string'}, 'merge_reason': {'type': 'string'}, 'gap_or_hypothesis_text': {'type': 'string'}, 'remaining_uncertainties': {'type': 'array', 'items': {'type': 'string'}}, 'target_id': {'type': 'string'}, 'action': {'type': 'string'}, 'category': {'type': 'string'}, 'perspective': {'type': 'string'}, 'argument': {'type': 'string'}, 'paper_references': {'type': 'array', 'items': {'type': 'object', 'properties': {'paper_id': {'type': 'string'}, 'sections': {'type': 'array', 'items': {'type': 'string'}}}, 'required': [], 'additionalProperties': False}}, 'proposed_revision': {'type': 'string'}, 'merge_with': {'type': 'array', 'items': {'type': 'string'}}, 'position': {'type': 'string'}, 'response': {'type': 'string'}, 'overall_response': {'type': 'string'}, 'revised_record': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': True}, 'relation': {'type': 'string'}, 'excludes': {'type': 'array', 'items': {'type': 'string'}}, 'owned_by': {'type': 'array', 'items': {'type': 'string'}}, 'boundary_rule': {'type': 'string'}, 'description': {'type': 'string'}, 'name': {'type': 'string'}, 'coverage_check': {'type': 'string'}, 'overlap_check': {'type': 'string'}, 'origin_perspective': {'type': 'string'}},
        "required": [],
        "additionalProperties": False,
    }
    def arr(item):
        return {"type": "array", "items": item}
    def obj(properties):
        return {"type": "object", "properties": properties,
                "required": list(properties), "additionalProperties": False}
    stages = {
        "paper_reading": obj({k: record["properties"][k] for k in (
            "paper_title","authors_year","research_question","context","methods",
            "main_findings","assumptions","limitations_explicit",
            "potential_open_questions","candidate_hypotheses")}),
        "paper_analysis": obj({k: record["properties"][k] for k in (
            "paper_title","authors_year","research_question","context","methods",
            "main_findings","assumptions","limitations_explicit",
            "potential_open_questions","candidate_hypotheses")}),
        "perspective_discovery": obj({
            "perspectives": arr(obj({k: record["properties"][k] for k in
                ("name","description","excludes","owned_by","boundary_rule","rationale")})),
            "coverage_check":{"type":"string"},"overlap_check":{"type":"string"}}),
        "research_gap_generation": obj({
            "perspective":{"type":"string"},
            "research_gaps":arr(obj({k:record["properties"][k] for k in (
                "gap","why_it_matters","what_is_known","what_remains_unknown","gap_type",
                "confidence","supporting_papers","evidence")}))}),
        "initial_gap_curation_and_corpus_analysis": obj({
            "research_gaps":arr(obj({k:record["properties"][k] for k in (
                "id","decision","merged_ids","reason","gap","why_it_matters","what_is_known",
                "what_remains_unknown","gap_type","confidence","origin_perspectives",
                "supporting_papers","related_papers","evidence")})),
            "rejected":arr(obj({"id":{"type":"string"},"reason":{"type":"string"}})),
            "curation_summary":{"type":"string"}}),
        "research_gap_challenger": obj({
            "proposed_changes":arr(obj({k:record["properties"][k] for k in (
                "target_id","action","category","perspective","argument","evidence",
                "paper_references","proposed_revision","merge_with")})),
            "no_change_reason":{"type":"string"}}),
        "hypothesis_challenger": obj({
            "proposed_changes":arr(obj({k:record["properties"][k] for k in (
                "target_id","action","category","perspective","argument","evidence",
                "paper_references","proposed_revision","merge_with")})),
            "no_change_reason":{"type":"string"}}),
        "research_gap_defender": obj({
            "responses":arr(obj({k:record["properties"][k] for k in (
                "target_id","position","response","evidence","paper_references","proposed_revision")})),
            "overall_response":{"type":"string"}}),
        "hypothesis_defender": obj({
            "responses":arr(obj({k:record["properties"][k] for k in (
                "target_id","position","response","evidence","paper_references","proposed_revision")})),
            "overall_response":{"type":"string"}}),
        "research_gap_adjudication": _adjudication_schema(record, obj),
        "hypothesis_adjudication": _adjudication_schema(record, obj),
        "hypothesis_generation": obj({
            "perspective":{"type":"string"},
            "hypotheses":arr(obj({k:record["properties"][k] for k in (
                "hypothesis","rationale","testable_prediction","proposed_test",
                "originating_gap_ids","supporting_papers","related_papers","evidence")}))}),

        # "final_curation": obj({
        #     "research_gaps":arr(record),"hypotheses":arr(record),
        #     "merged_or_rejected":arr(record),"curation_summary":{"type":"string"}}),

        # "final_curation": obj({
        #     "research_gaps": arr(obj({
        #         "id": {"type": "string"}
        #     })),
        #     "hypotheses": arr(obj({
        #         "id": {"type": "string"}
        #     })),
        #     "merged_or_rejected": arr(obj({
        #         "id": {"type": "string"}
        #     })),
        #     "curation_summary": {"type": "string"}
        # }),

        "final_curation": obj({
            "research_gaps": arr(obj({
                "id": {"type": "string"},
                "gap": {"type": "string"},
                "why_it_matters": {"type": "string"},
                "what_is_known": {"type": "string"},
                "what_remains_unknown": {"type": "string"},
                "gap_type": {"type": "string"},
                "confidence": {"type": "string"},
                "supporting_papers": record["properties"]["supporting_papers"],
                "related_papers": record["properties"]["related_papers"],
                "evidence": record["properties"]["evidence"]
            })),
            "hypotheses": arr(obj({
                "id": {"type": "string"},
                "hypothesis": {"type": "string"},
                "rationale": {"type": "string"},
                "testable_prediction": {"type": "string"},
                "proposed_test": {"type": "string"},
                "originating_gap_ids": {"type": "array", "items": {"type": "string"}},
                "supporting_papers": record["properties"]["supporting_papers"],
                "related_papers": record["properties"]["related_papers"],
                "evidence": record["properties"]["evidence"]
            })),
            "merged_or_rejected": arr(obj({
                "id": {"type": "string"},
                "reason": {"type": "string"}
            })),
            "curation_summary": {"type": "string"}
        }),

        "hypothesis_synthesis": obj({
            "historical_analysis":{"type":"string"},
            "research_gaps":arr(record),"hypotheses":arr(record)}),
        "self_critique": obj({
            "proposed_changes":arr(obj({k:record["properties"][k] for k in (
                "target_id","action","category","argument","evidence","paper_references",
                "proposed_revision","merge_with")})),
            "no_change_reason":{"type":"string"}}),
        "self_critique_revision": _adjudication_schema(record, obj),
    }
    try:
        return stages[stage]
    except KeyError:
        raise ValueError(f"No structured-output schema registered for stage: {stage}")


def _adjudication_schema(record, obj):
    def arr(item):
        return {"type":"array","items":item}
    revised_props = {k: record["properties"][k] for k in (
        "id","gap","hypothesis","gap_or_hypothesis_text","why_it_matters","what_is_known",
        "what_remains_unknown","rationale","testable_prediction","proposed_test",
        "supporting_papers","related_papers","evidence")}
    revised = {"type":"object","properties":revised_props,"required":[],
               "additionalProperties":False}
    decision = obj({
        "target_id":{"type":"string"},"decision":{"type":"string"},"reason":{"type":"string"},
        "merged_ids":arr({"type":"string"}),"revised_record":revised,
        "remaining_uncertainties":arr({"type":"string"})})
    return obj({"decisions":arr(decision),"round_summary":{"type":"string"}})


class _Runner:
    """Throttling, retries, usage and inference-history logging for every API call."""

    def __init__(self, llm, model_name, prices, pause_sec, max_retries, max_rounds):
        self.llm = llm
        self.model_name = model_name
        self.prices = prices or {}
        self.pause_sec = pause_sec
        self.max_retries = max_retries
        self.max_rounds = max_rounds
        self.history = []
        self.usage = []
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

    def call(self, prompt, *, stage, agent, paper_path=None, round_no=None):
        """One LLM request. Returns the parsed JSON dict, or None on failure."""
        event = {
            "event_id": f"E{len(self.history)+1:04d}", "timestamp_utc": _now(),
            "stage": stage, "agent": agent, "round": round_no,
            "paper_loc": str(Path(paper_path).resolve()) if paper_path else None,
            "prompt": prompt, "status": "started",
        }
        self.history.append(event)
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
            _print_call_result(stage, agent, None, event.get("paper_loc"), error=event["error"])
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
                response = structured_result.get("raw")
                parsed = structured_result.get("parsed")
                parsing_error = structured_result.get("parsing_error")
                runtime = round(time.perf_counter() - started, 3)
                self._last_done = time.monotonic()
                usage = getattr(response, "usage_metadata", None) or {}
                inp, out = usage.get("input_tokens"), usage.get("output_tokens")
                total = usage.get("total_tokens")
                if total is None and inp is not None and out is not None:
                    total = inp + out
                cost = None
                if (inp is not None and out is not None and self.prices.get("input") is not None
                        and self.prices.get("output") is not None):
                    cost = (inp * self.prices["input"] + out * self.prices["output"]) / 1_000_000
                self.usage.append({
                    "timestamp_utc": _now(), "stage": stage, "agent": agent,
                    "round": round_no, "paper_loc": event["paper_loc"],
                    "model": self.model_name, "attempt": attempt, "status": "success",
                    "runtime_seconds": runtime, "input_tokens": inp,
                    "output_tokens": out, "total_tokens": total,
                    "estimated_cost_usd": cost, "error": None,
                })
                raw = _text(response.content) if response is not None else ""
                if hasattr(parsed, "model_dump"):
                    parsed = parsed.model_dump()
                if not isinstance(parsed, dict):
                    parsed = None
                event.update(status="success" if parsed is not None else "parse_error",
                             response=raw, parsed_output=parsed,
                             structured_output_error=str(parsing_error) if parsing_error else None,
                             runtime_seconds=runtime, attempts=attempt)
                if parsed is None:
                    event["parse_warning"] = (
                        "Gemini structured output did not produce a parsed object: "
                        + (str(parsing_error) if parsing_error else "unknown parsing error"))
                _print_call_result(stage, agent, parsed, event.get("paper_loc"), runtime)
                return parsed
            except Exception as exc:
                runtime = round(time.perf_counter() - started, 3)
                self._last_done = time.monotonic()
                error = f"{type(exc).__name__}: {exc}"
                self.usage.append({
                    "timestamp_utc": _now(), "stage": stage, "agent": agent,
                    "round": round_no, "paper_loc": event["paper_loc"],
                    "model": self.model_name, "attempt": attempt, "status": "error",
                    "runtime_seconds": runtime, "input_tokens": None,
                    "output_tokens": None, "total_tokens": None,
                    "estimated_cost_usd": None, "error": error,
                })
                retryable = any(term in str(exc).lower() for term in _RETRYABLE_TERMS)
                if retryable and attempt < self.max_retries:
                    backoff = self.pause_sec * (2 ** (attempt - 1))
                    print(f"[WAIT] {backoff:.1f}s before retrying {agent}")
                    time.sleep(backoff)
                    self._last_done = time.monotonic()
                    continue
                event.update(status="error", error=error, runtime_seconds=runtime,
                             attempts=attempt)
                _print_call_result(stage, agent, None, event.get("paper_loc"), error=error)
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


def _challenger_prompt(topic, kind, rnd, max_rounds, records, perspectives, cards):
    return f"""
ROLE: Scientific Challenger
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{max_rounds}
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


def _defender_prompt(topic, kind, rnd, max_rounds, records, challenges, cards):
    return f"""
ROLE: Scientific Defender
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{max_rounds}
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


def _adjudicator_prompt(topic, kind, rnd, max_rounds, records, challenges, defences):
    return f"""
ROLE: Scientific Adjudicator
TOPIC: {topic}; SUBJECT: {kind}; ROUND: {rnd}/{max_rounds}
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


def _apply_initial_curation(records, parsed, valid_ids, runner):
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
            runner.note("curation_integrity_warning", "warning", f"{rec['id']} omitted; retained.")
    return active, rejected


def _active(records):
    return [x for x in records if x.get("status") not in ("rejected", "merged")]


def _apply_revision(rec, revised, key, valid_ids):
    """Apply an adjudicator revised_record to rec. Empty values never wipe existing content."""
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
    rec["related_papers"] += _normal_related(revised.get("related_papers"), valid_ids)
    return True


def _apply_decisions(records, decisions, changes, responses, rnd, kind, valid_ids, rejected):
    """Apply the adjudicator's decisions to the active records (mutates them in place)."""
    key = "gap" if kind == "research_gap" else "hypothesis"
    by_id = {x["id"]: x for x in records}
    for decision in decisions if isinstance(decisions, list) else []:
        if not isinstance(decision, dict):
            continue
        rid = decision.get("target_id")
        rec = by_id.get(rid)
        if not rec or rec.get("status") in ("rejected", "merged"):
            continue
        decision["round"] = rnd
        rec.setdefault("debate_history", []).append({
            "round": rnd,
            "challenge": [x for x in changes if isinstance(x, dict) and x.get("target_id") == rid],
            "defence": [x for x in responses if isinstance(x, dict) and x.get("target_id") == rid],
            "decision": decision,
        })
        action = decision.get("decision", "retain")
        rec["last_decision"] = decision
        if action == "reject":
            rec.update(status="rejected", rejection_reason=decision.get("reason", ""))
            rejected.append(rec)
        elif action in ("merge", "revise"):
            if action == "merge":
                # The target keeps its ID and survives; only the absorbed records leave.
                absorbed_ids = [
                    str(m) for m in _as_list(decision.get("merged_ids"))
                    if str(m) in by_id and str(m) != rid
                    and by_id[str(m)].get("status") not in ("rejected", "merged")
                ]
                rec["merged_ids"] = list(dict.fromkeys(rec.get("merged_ids", []) + absorbed_ids))
                for mid in absorbed_ids:
                    absorbed = by_id[mid]
                    rec["supporting_papers"] = _merge_refs(
                        rec.get("supporting_papers"), absorbed.get("supporting_papers"))
                    rec["related_papers"] += absorbed.get("related_papers", [])
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


def _run_debate(runner, topic, kind, records, perspectives, cards, valid_ids):
    rounds, rejected = [], []
    for rnd in range(1, runner.max_rounds + 1):
        current = _active(records)
        if not current:
            break
        challenges = runner.call(
            _challenger_prompt(topic, kind, rnd, runner.max_rounds, current, perspectives, cards),
            stage=f"{kind}_challenger", agent=f"{kind.title()} Challenger", round_no=rnd,
        ) or {}
        changes = challenges.get("proposed_changes", [])
        changes = [x for x in changes if isinstance(x, dict)] if isinstance(changes, list) else []
        if not changes:
            runner.note(f"{kind}_debate_terminated", "success",
                        "No challenger changes; defender, adjudicator and later rounds skipped.",
                        round=rnd)
            rounds.append({"round": rnd, "challenges": [], "terminated": True,
                           "reason": challenges.get("no_change_reason", "")})
            break

        defences = runner.call(
            _defender_prompt(topic, kind, rnd, runner.max_rounds, current, changes, cards),
            stage=f"{kind}_defender", agent=f"{kind.title()} Defender", round_no=rnd,
        ) or {}
        responses = defences.get("responses", [])
        adjudication = runner.call(
            _adjudicator_prompt(topic, kind, rnd, runner.max_rounds, current, changes, responses),
            stage=f"{kind}_adjudication", agent=f"{kind.title()} Adjudicator", round_no=rnd,
        ) or {}
        decisions = adjudication.get("decisions", [])
        _apply_decisions(current, decisions, changes, responses if isinstance(responses, list) else [],
                         rnd, kind, valid_ids, rejected)
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
                     price_per_million_tokens=None, *, max_rounds, pause_sec, max_retries):
    """Existing main.py-compatible entry point; returns data and logs only."""
    if not topic or not str(topic).strip():
        raise ValueError("topic cannot be empty.")
    paths = [Path(p).resolve() for p in pdf_paths]
    if not paths:
        raise ValueError("pdf_paths must contain at least one PDF.")
    runner = _Runner(llm, model_name, price_per_million_tokens, pause_sec, max_retries, max_rounds)
    started = time.perf_counter()
    papers = []

    # 1. Reader: one independent call per paper.
    print(f"[READER] Reading {len(paths)} papers sequentially.")
    for index, path in enumerate(paths, 1):
        pid = f"P{index:03d}"
        parsed = runner.call(
            _reader_prompt(topic, additional_prompt, pid, path),
            stage="paper_reading", agent="Literature Reader", paper_path=path,
        )
        if not isinstance(parsed, dict):
            runner.note("paper_reading_skipped", "warning",
                        "Paper failed or returned invalid JSON.",
                        paper_id=pid, paper_loc=str(path))
            continue
        papers.append({"paper_id": pid, "paper_loc": str(path),
                       "paper_filename": path.name, "analysis": parsed})
    if not papers:
        raise RuntimeError("No paper could be read successfully.")
    cards = _paper_cards(papers)
    valid_ids = {x["paper_id"] for x in cards}

    # 2. Topic-adaptive perspective finder.
    perspective_data = runner.call(
        _finder_prompt(topic, additional_prompt, cards),
        stage="perspective_discovery", agent="Topic-Adaptive Perspective Finder",
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
        parsed = runner.call(
            _gap_prompt(topic, additional_prompt, perspective, cards),
            stage="research_gap_generation",
            agent=f"{perspective['name']} Gap Generator",
        ) or {}
        new, next_id = _new_records(
            parsed.get("research_gaps", []), "G", next_id,
            perspective["name"], valid_ids)
        candidates.extend(new)

    # 4. Curator/analyser checks every candidate against every paper card.
    curated = runner.call(
        _curator_prompt(topic, candidates, cards),
        stage="initial_gap_curation_and_corpus_analysis",
        agent="Research-Gap Curator and Corpus Analyser",
    ) or {}
    gaps, rejected_gaps = _apply_initial_curation(candidates, curated, valid_ids, runner)

    # 5. Gap debate.
    gaps, debate_rejected, gap_rounds = _run_debate(
        runner, topic, "research_gap", gaps, perspectives, cards, valid_ids)
    rejected_gaps.extend(debate_rejected)

    # 6. Hypothesis generation: one call per perspective, IDs global.
    hypotheses, next_hid = [], 1
    if gaps:
        for perspective in perspectives:
            parsed = runner.call(
                _hypothesis_prompt(topic, additional_prompt, perspective, gaps, cards),
                stage="hypothesis_generation",
                agent=f"{perspective['name']} Hypothesis Generator",
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
        runner, topic, "hypothesis", hypotheses, perspectives, cards, valid_ids)

    # 8. Final curation. Fail-safe preserves IDs and records omitted by curator.
    final_data = runner.call(
        _final_prompt(topic, gaps, hypotheses),
        stage="final_curation", agent="Final Output Curator",
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

    successful = [x for x in runner.usage if x["status"] == "success"]
    costs = [x["estimated_cost_usd"] for x in successful
             if x["estimated_cost_usd"] is not None]
    summary = {
        "api_calls_logged": len(runner.usage), "successful_calls": len(successful),
        "failed_calls": len(runner.usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "note": "Pipeline usage only; not account-wide quota.",
    }
    runner.note("final_result", "success",
                f"{len(final_gaps)} gaps and {len(final_hypotheses)} hypotheses.")
    return {
        "agent_params": {
            "mode": "multi", "topic": topic,
            "additional_prompt": additional_prompt, "model": model_name,
            "papers": [{"paper_id": p["paper_id"], "paper_loc": p["paper_loc"]}
                       for p in papers],
            "perspectives": perspectives, "debate_rounds_max": max_rounds,
            "debate_termination": "Stop when challenger proposes no changes.",
            "execution": "Sequential API calls; no concurrent requests.",
            "pause_after_response_seconds": pause_sec, "max_retries": max_retries,
            "web_search": False,
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
        "usage_summary": summary, "api_usage": runner.usage,
        "inference_history": runner.history,
        "inference_history_text": _history_text(topic, runner.history),
    }
