"""Single-LLM research-gap and hypothesis-generation pipeline.

Stages:
1. Analyze each PDF separately.
2. Synthesize the paper analyses into draft gaps and hypotheses.
3. Perform one self-critique and one refinement.

This module returns data and logs; main.py owns file output.
"""

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

pause_sec = 5
MAX_RETRIES = 3
_last_request_completed_at = None


def _usage_from_response(response):
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens


def _response_to_text(content):
    if isinstance(content, str):
        return content
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
    return str(content)


def _wait_after_previous_response():
    global _last_request_completed_at
    if _last_request_completed_at is None:
        return
    remaining = pause_sec - (time.monotonic() - _last_request_completed_at)
    if remaining > 0:
        print(f"Waiting {remaining:.1f}s before the next model request.")
        time.sleep(remaining)


def _is_retryable_error(exc):
    message = str(exc).lower()
    return any(term in message for term in (
        "429", "resource_exhausted", "rate limit", "too many requests",
        "503", "service unavailable", "502", "504",
    ))


def _invoke(llm, prompt, model_name, price_table, stage,
            inference_history, api_usage, paper_loc=None, pdf_path=None):
    global _last_request_completed_at

    event = {
        "event_id": f"E{len(inference_history)+1:04d}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage, "agent": "Single Researcher", "paper_loc": paper_loc,
        "prompt": prompt, "status": "started",
    }
    inference_history.append(event)

    try:
        if pdf_path is None:
            message = HumanMessage(content=prompt)
        else:
            pdf_path = Path(pdf_path)
            encoded_pdf = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
            ])
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        event.update({"status": "error", "error": error})
        print(f"[ERROR] Could not prepare {paper_loc or stage}: {error}")
        return None

    for attempt in range(1, MAX_RETRIES + 1):
        _wait_after_previous_response()
        start = time.perf_counter()
        try:
            response = llm.invoke([message])
        except Exception as exc:
            runtime = round(time.perf_counter() - start, 3)
            _last_request_completed_at = time.monotonic()
            error = f"{type(exc).__name__}: {exc}"
            api_usage.append({
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "stage": stage, "paper_loc": paper_loc, "model": model_name,
                "attempt": attempt, "status": "error", "runtime_seconds": runtime,
                "input_tokens": None, "output_tokens": None, "total_tokens": None,
                "estimated_cost_usd": None, "error": error,
            })
            if _is_retryable_error(exc) and attempt < MAX_RETRIES:
                backoff = pause_sec * (2 ** (attempt - 1))
                print(f"[RETRY] {stage}, attempt {attempt}/{MAX_RETRIES}; retrying in {backoff}s: {error}")
                time.sleep(backoff)
                _last_request_completed_at = time.monotonic()
                continue
            event.update({"status": "error", "error": error, "attempts": attempt})
            print(f"[ERROR] {stage} failed: {error}")
            return None

        runtime = round(time.perf_counter() - start, 3)
        _last_request_completed_at = time.monotonic()
        input_tokens, output_tokens, total_tokens = _usage_from_response(response)
        cost = None
        prices = price_table or {}
        if input_tokens is not None and output_tokens is not None:
            if prices.get("input") is not None and prices.get("output") is not None:
                cost = (
                    input_tokens * prices["input"] + output_tokens * prices["output"]
                ) / 1_000_000

        api_usage.append({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": stage, "paper_loc": paper_loc, "model": model_name,
            "attempt": attempt, "status": "success", "runtime_seconds": runtime,
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "total_tokens": total_tokens, "estimated_cost_usd": cost, "error": None,
        })
        content = _response_to_text(response.content)
        event.update({
            "status": "success", "response": content,
            "runtime_seconds": runtime, "attempts": attempt,
        })
        return content
    return None


def _parse_json_response(text):
    cleaned = _response_to_text(text).strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(cleaned[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {
        "historical_analysis": cleaned,
        "research_gaps": [],
        "hypotheses": [],
        "parse_warning": "Invalid JSON; raw response is retained in inference_history.",
    }


def _normalise_result(parsed, valid_papers):
    gaps = parsed.get("research_gaps", [])
    hypotheses = parsed.get("hypotheses", [])
    if not isinstance(gaps, list): gaps = [gaps]
    if not isinstance(hypotheses, list): hypotheses = [hypotheses]

    def refs_for(values):
        refs = []
        if not isinstance(values, list): values = [values] if values else []
        for value in values:
            loc = value.get("paper_loc") if isinstance(value, dict) else value
            if loc:
                pid = valid_papers.get(str(Path(str(loc)).resolve()))
                if pid: refs.append({"paper_id": pid, "sections": [], "evidence": ""})
        return refs

    gap_records = []
    for i, item in enumerate(gaps, 1):
        item = item if isinstance(item, dict) else {"gap": str(item)}
        gap_records.append({
            "id": f"G{i:03d}", "gap": item.get("gap", ""),
            "why_it_matters": item.get("why_it_matters", item.get("why_unresolved", "")),
            "what_is_known": item.get("what_is_known", ""),
            "what_remains_unknown": item.get("what_remains_unknown", item.get("why_unresolved", "")),
            "gap_type": item.get("gap_type", "unspecified"), "confidence": item.get("confidence"),
            "evidence": item.get("evidence", ""), "origin_perspective": None,
            "origin_perspectives": [], "supporting_papers": refs_for(item.get("supporting_papers", [])),
            "related_papers": [], "status": "accepted",
        })
    hypothesis_records = []
    for i, item in enumerate(hypotheses, 1):
        item = item if isinstance(item, dict) else {"hypothesis": str(item)}
        hypothesis_records.append({
            "id": f"H{i:03d}", "hypothesis": item.get("hypothesis", ""),
            "rationale": item.get("rationale", ""),
            "supporting_papers": refs_for(item.get("supporting_papers", [])),
            "origin_perspective": None, "origin_perspectives": [],
            "originating_gap_ids": item.get("originating_gap_ids", []),
            "testable_prediction": item.get("testable_prediction", ""),
            "caveats": item.get("caveats", ""), "status": "accepted",
        })
    return {
        "historical_analysis": parsed.get("historical_analysis", ""),
        "research_gaps": [
            f"{x['id']}: {x['gap']}" + (
                " [Papers: " + "; ".join(r["paper_id"] for r in x["supporting_papers"]) + "]"
                if x["supporting_papers"] else ""
            ) for x in gap_records
        ],
        "research_gap_records": gap_records, "hypotheses": hypothesis_records,
        "self_critique": parsed.get("self_critique", ""),
        "parse_warning": parsed.get("parse_warning"),
    }


def _history_text(topic, events):
    lines = ["=" * 80, "ATR SINGLE-AGENT INFERENCE HISTORY", f"Topic: {topic}",
             f"Generated: {datetime.now(timezone.utc).isoformat()}", "=" * 80, ""]
    for e in events:
        head = f"[{e.get('event_id')}] {e.get('stage')} | {e.get('agent')}"
        lines += [head, "-" * min(len(head), 80)]
        if e.get("paper_loc"): lines.append(f"Paper: {e['paper_loc']}")
        if e.get("status"): lines.append(f"Status: {e['status']}")
        if e.get("message"): lines.append(e["message"])
        if e.get("error"): lines.append(f"Error: {e['error']}")
        if e.get("response"): lines += ["", e["response"]]
        lines.append("")
    return "\n".join(lines)


def run_single_agent(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    """Run the single-agent pipeline and return results/logs to main.py."""
    global _last_request_completed_at
    _last_request_completed_at = None

    price_table = price_per_million_tokens or {}
    inference_history, api_usage, paper_analyses = [], [], []
    total_start = time.perf_counter()
    pdf_paths = [Path(path).resolve() for path in pdf_paths]
    total_papers = len(pdf_paths)

    # Stage 1: each paper is analyzed in its own sequential request.
    for index, pdf_path in enumerate(pdf_paths, start=1):
        paper_loc = str(pdf_path)
        print(f"Sent paper {pdf_path.name} to model ({index}/{total_papers}).")
        prompt = f"""
You are a careful scientific research assistant.
Research topic: {topic}
Additional user instructions: {additional_prompt or 'None'}
Paper filename: {pdf_path.name}

Read the attached PDF directly. Analyze ONLY this paper. Do not invent facts.
Return ONLY valid JSON using this schema:
{{
  "paper_title": "", "authors_year": "", "research_question": "",
  "context": "", "methods": [], "main_findings": [], "assumptions": [],
  "limitations_explicit": [], "potential_open_questions": [],
  "candidate_hypotheses": []
}}
Separate explicit statements from inference. Capture section/page references
where possible. Do not claim novelty beyond this paper.
"""
        content = _invoke(
            llm, prompt, model_name, price_table, "paper_analysis",
            inference_history, api_usage, paper_loc=paper_loc, pdf_path=pdf_path,
        )
        if content is None:
            print(f"Could not analyse {pdf_path.name}; skipping this paper.")
            inference_history.append({
                "event_id": f"E{len(inference_history)+1:04d}",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "stage": "paper_analysis_skipped", "agent": "Orchestrator",
                "paper_id": f"P{index:03d}", "paper_loc": paper_loc,
                "status": "warning", "message": "No analysis generated for this paper.",
            })
            continue
        paper_data = _parse_json_response(content)
        if "parse_warning" in paper_data:
            paper_data = {"raw_analysis": content}
        paper_analyses.append({"paper_id": f"P{len(paper_analyses)+1:03d}",
                               "paper_loc": paper_loc, "paper_filename": pdf_path.name,
                               "analysis": paper_data})
        print(f"Analysed {pdf_path.name} ({index}/{total_papers}).")
        inference_history.append({
            "event_id": f"E{len(inference_history)+1:04d}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": "paper_analysis_log", "agent": "Orchestrator",
            "paper_id": paper_analyses[-1]["paper_id"], "paper_loc": paper_loc,
            "status": "success", "message": f"Analysed: {pdf_path.name}",
        })

    parsed = {"historical_analysis": "", "research_gaps": [], "hypotheses": []}

    # Stage 2: synthesize all successful paper analyses.
    if paper_analyses:
        synthesis_prompt = f"""
You are a single scientific researcher synthesizing a supplied literature corpus.
Research topic: {topic}
Additional user instructions: {additional_prompt or 'None'}

Use ONLY the paper analyses below as evidence. Do not imply that this corpus
represents all published literature. Distinguish explicit findings, reasonable
inferences, and speculation.

Produce:
1. A concise historical account of the research area's development.
2. Specific research gaps. Explain what remains unresolved and identify
   supporting paper paths. Consider the entire supplied corpus.
3. Specific, falsifiable candidate hypotheses. For each give rationale,
   supporting paper paths, a testable prediction, and caveats.

Do not call something a research gap merely because one paper does not discuss
it. Avoid duplicate or overlapping gaps and hypotheses.

Return ONLY valid JSON, no Markdown:
{{
  "historical_analysis": "string",
  "research_gaps": [
    {{
      "gap": "Specific unresolved research gap",
      "supporting_papers": ["/absolute/path/to/paper.pdf"],
      "evidence": "Evidence from supplied analyses",
      "why_unresolved": "Why the corpus leaves this unresolved"
    }}
  ],
  "hypotheses": [
    {{
      "hypothesis": "Specific, falsifiable hypothesis",
      "rationale": "Evidence-based rationale",
      "supporting_papers": ["/absolute/path/to/paper.pdf"],
      "testable_prediction": "Observable prediction",
      "caveats": "Assumptions, limitations, or counterevidence"
    }}
  ]
}}

PAPER ANALYSES:
{json.dumps(paper_analyses, ensure_ascii=False)}
"""
        print("Sending paper analyses for cross-paper synthesis.")
        synthesis = _invoke(
            llm, synthesis_prompt, model_name, price_table, "hypothesis_synthesis",
            inference_history, api_usage,
        )

        if synthesis is not None:
            # Stage 3: exactly one self-critique and one refinement.
            critique_prompt = f"""
You are the SAME single researcher who produced the draft below.
Perform exactly ONE self-critique and ONE refinement. Do not simulate other
agents, personas, reviewers, or a debate.

Research topic: {topic}
Additional user instructions: {additional_prompt or 'None'}

First, identify:
- Unsupported claims
- Gaps already addressed by another paper in the corpus
- Gaps based only on absence of discussion
- Vague, non-falsifiable, or restated hypotheses
- Duplicate or overlapping gaps/hypotheses
- Hidden assumptions, contradictory evidence, and feasibility concerns
- Incorrect or unsupported paper references

Then revise the draft ONCE using that critique. Preserve valid content,
correct weak content, and remove unsupported claims. Do not critique the
revised version again.

Return ONLY valid JSON, no Markdown:
{{
  "historical_analysis": "Refined historical analysis",
  "self_critique": {{
    "issues_identified": ["Issue identified"],
    "changes_made": ["Change made in the one refinement"]
  }},
  "research_gaps": [
    {{
      "gap": "Specific unresolved research gap",
      "supporting_papers": ["/absolute/path/to/paper.pdf"],
      "evidence": "Evidence from supplied analyses",
      "why_unresolved": "Why the corpus leaves this unresolved"
    }}
  ],
  "hypotheses": [
    {{
      "hypothesis": "Specific, falsifiable hypothesis",
      "rationale": "Evidence-based rationale",
      "supporting_papers": ["/absolute/path/to/paper.pdf"],
      "testable_prediction": "Observable prediction",
      "caveats": "Assumptions, limitations, or counterevidence"
    }}
  ]
}}

Do not claim novelty beyond the supplied papers. A broader literature review
would be required to establish novelty.

DRAFT:
{synthesis}

SUPPLIED PAPER ANALYSES:
{json.dumps(paper_analyses, ensure_ascii=False)}
"""
            print("Performing one self-critique and one refinement.")
            final_raw = _invoke(
                llm, critique_prompt, model_name, price_table,
                "self_critique_refinement", inference_history, api_usage,
            )
            if final_raw is not None:
                valid_papers = {p["paper_loc"]: p["paper_id"] for p in paper_analyses}
                parsed = _normalise_result(_parse_json_response(final_raw), valid_papers)
            else:
                valid_papers = {p["paper_loc"]: p["paper_id"] for p in paper_analyses}
                parsed = _normalise_result(_parse_json_response(synthesis), valid_papers)
                parsed["critique_warning"] = (
                    "Critique/refinement request failed; using synthesis without refinement."
                )
        else:
            parsed["synthesis_warning"] = "Cross-paper synthesis request failed."
    else:
        parsed["analysis_warning"] = "No papers were successfully analysed."

    successful = [item for item in api_usage if item["status"] == "success"]
    costs = [
        item["estimated_cost_usd"] for item in successful
        if item["estimated_cost_usd"] is not None
    ]
    usage_summary = {
        "api_calls_logged": len(api_usage),
        "successful_calls": len(successful),
        "failed_calls": len(api_usage) - len(successful),
        "input_tokens": sum(item["input_tokens"] or 0 for item in successful),
        "output_tokens": sum(item["output_tokens"] or 0 for item in successful),
        "total_tokens": sum(item["total_tokens"] or 0 for item in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - total_start, 3),
    }

    inference_history.append({
        "event_id": f"E{len(inference_history)+1:04d}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "final_result", "agent": "Orchestrator", "status": "success",
        "message": f"{len(parsed.get('research_gap_records', []))} gaps and {len(parsed.get('hypotheses', []))} hypotheses.",
    })
    return {
        "agent_params": {
            "mode": "single", "topic": topic, "additional_prompt": additional_prompt,
            "model": model_name,
            "papers": [{"paper_id": p["paper_id"], "paper_loc": p["paper_loc"]} for p in paper_analyses],
            "perspectives": [], "debate_rounds_max": 0,
            "debate_termination": "Not applicable; one self-critique and refinement.",
            "execution": "Sequential API calls; no concurrent requests.",
            "pause_after_response_seconds": pause_sec, "web_search": False,
            "self_critique_rounds": 1, "refinement_rounds": 1,
        },
        "paper_analyses": paper_analyses, "perspective_finder_output": None,
        "historical_analysis": parsed.get("historical_analysis", ""),
        "research_gaps": parsed.get("research_gaps", []),
        "research_gap_records": parsed.get("research_gap_records", []),
        "hypotheses": parsed.get("hypotheses", []),
        "rejected_research_gaps": [], "rejected_hypotheses": [],
        "debate_summaries": {"research_gaps": [], "hypotheses": []},
        "curation": {"initial": None, "final_summary": parsed.get("self_critique", ""),
                     "merged_or_rejected": []},
        "self_critique": parsed.get("self_critique", ""),
        "parse_warning": parsed.get("parse_warning"),
        "synthesis_warning": parsed.get("synthesis_warning"),
        "critique_warning": parsed.get("critique_warning"),
        "analysis_warning": parsed.get("analysis_warning"),
        "usage_summary": usage_summary, "api_usage": api_usage,
        "inference_history": inference_history,
        "inference_history_text": _history_text(topic, inference_history),
    }
