"""Single-LLM PDF analysis pipeline. Returns logs to main.py; writes no files."""

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage

# Minimum pause after a response completes and before the next API request.
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
    """Normalize LangChain string/list content for the next pipeline stage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("text") is not None:
                    parts.append(str(block["text"]))
            elif isinstance(block, str):
                parts.append(block)
            elif getattr(block, "text", None) is not None:
                parts.append(str(block.text))
        return "\n".join(parts).strip()
    return str(content)


def _wait_after_previous_response():
    """Ensure pause_sec elapses after the previous request has completed."""
    global _last_request_completed_at

    if _last_request_completed_at is None:
        return

    elapsed = time.monotonic() - _last_request_completed_at
    remaining = pause_sec - elapsed
    if remaining > 0:
        print(f"Waiting {remaining:.1f}s before the next model request.")
        time.sleep(remaining)


def _is_retryable_error(exc):
    message = str(exc).lower()
    return any(term in message for term in (
        "429", "resource_exhausted", "rate limit", "too many requests",
        "503", "service unavailable", "502", "504",
    ))


def _invoke_pdf(llm, pdf_path, prompt, model_name, price_table, stage,
                inference_history, api_usage, paper=None):
    global _last_request_completed_at

    timestamp = datetime.now(timezone.utc).isoformat()
    event = {
        "timestamp_utc": timestamp,
        "stage": stage,
        "paper": paper,
        "prompt": prompt,
        "status": "started",
    }
    inference_history.append(event)

    try:
        if pdf_path is None:
            message = HumanMessage(content=prompt)
        else:
            encoded_pdf = base64.b64encode(Path(pdf_path).read_bytes()).decode("ascii")
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
            ])
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        event.update({"status": "error", "error": error})
        print(f"[ERROR] Could not prepare {paper or stage}: {error}")
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
                "stage": stage,
                "paper": paper,
                "model": model_name,
                "attempt": attempt,
                "status": "error",
                "runtime_seconds": runtime,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "estimated_cost_usd": None,
                "error": error,
            })

            if _is_retryable_error(exc) and attempt < MAX_RETRIES:
                backoff = pause_sec * (2 ** (attempt - 1))
                print(
                    f"[RETRY] {stage}, attempt {attempt}/{MAX_RETRIES}; "
                    f"backoff {backoff}s. Error: {error}"
                )
                time.sleep(backoff)
                # Keep the required pause_sec separate from retry backoff.
                _last_request_completed_at = time.monotonic()
                continue

            event.update({"status": "error", "error": error, "attempts": attempt})
            print(f"[ERROR] {stage} failed: {error}")
            return None

        runtime = round(time.perf_counter() - start, 3)
        _last_request_completed_at = time.monotonic()

        input_tokens, output_tokens, total_tokens = _usage_from_response(response)
        prices = price_table or {}
        cost = None
        if input_tokens is not None and output_tokens is not None:
            if prices.get("input") is not None and prices.get("output") is not None:
                cost = (
                    input_tokens * prices["input"]
                    + output_tokens * prices["output"]
                ) / 1_000_000

        api_usage.append({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "paper": paper,
            "model": model_name,
            "attempt": attempt,
            "status": "success",
            "runtime_seconds": runtime,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost,
            "error": None,
        })

        content = _response_to_text(response.content)
        event.update({
            "status": "success",
            "response": content,
            "runtime_seconds": runtime,
            "attempts": attempt,
        })
        return content

    return None


def deduplicate_hypotheses(hypotheses):
    """Placeholder for future local cosine-similarity filtering."""
    return hypotheses


def _parse_final_output(text):
    text = _response_to_text(text)
    cleaned = text.strip()

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

    return {
        "historical_analysis": text,
        "research_gaps": [],
        "hypotheses": [],
        "parse_warning": (
            "Model response was not valid JSON; raw response is in inference_history."
        ),
    }


def run_single_agent(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    global _last_request_completed_at

    # Reset timing state for each pipeline run.
    _last_request_completed_at = None

    price_table = price_per_million_tokens or {}
    inference_history = []
    api_usage = []
    paper_analyses = []
    total_start = time.perf_counter()
    total_papers = len(pdf_paths)

    # Each PDF is sent in its own sequential request.
    for index, pdf_path in enumerate(pdf_paths, start=1):
        pdf_path = Path(pdf_path)
        print(f"Sent paper {pdf_path.name} to model ({index}/{total_papers}).")

        prompt = f"""
You are assisting with scientific hypothesis generation.
Research topic: {topic}
Additional user instructions: {additional_prompt or 'None'}
Paper filename: {pdf_path.name}

Read the attached PDF directly. Analyze ONLY this paper and do not invent facts.
Return: (1) context and research question, (2) methods and findings, (3) limitations,
(4) relevant research gaps, (5) candidate scientific hypotheses, and (6) supporting
evidence and page/section references where possible. Be concise but useful for synthesis.
"""

        content = _invoke_pdf(
            llm, pdf_path, prompt, model_name, price_table,
            "paper_analysis", inference_history, api_usage, pdf_path.name,
        )

        if content is None:
            print(f"Could not analyse {pdf_path.name}; skipping this paper.")
            inference_history.append({
                "stage": "paper_analysis_skipped",
                "paper": pdf_path.name,
                "message": "No analysis generated for this paper.",
            })
            continue

        paper_analyses.append({"paper": pdf_path.name, "analysis": content})
        print(f"Analysed {pdf_path.name} ({index}/{total_papers}).")
        inference_history.append({
            "stage": "paper_analysis_log",
            "paper": pdf_path.name,
            "message": f"Analysed: {pdf_path.name}",
        })

    parsed = {"historical_analysis": "", "research_gaps": [], "hypotheses": []}

    if paper_analyses:
        synthesis_prompt = f"""
Synthesize the following paper-level analyses for the topic: {topic}
Additional instructions: {additional_prompt or 'None'}
Use only supplied evidence; distinguish speculation. Return ONLY valid JSON, no Markdown,
with exactly this structure:
{{
  "historical_analysis": "Concise account of how the research area developed",
  "research_gaps": ["Specific gap with supporting paper filenames"],
  "hypotheses": [{{
    "hypothesis": "Specific, falsifiable hypothesis",
    "rationale": "Evidence-based rationale",
    "supporting_papers": ["paper.pdf"],
    "testable_prediction": "Possible test",
    "caveats": "Assumptions or counterevidence"
  }}]
}}
Do not claim novelty beyond these papers; broader literature review is required to establish novelty.
PAPER ANALYSES:
{json.dumps(paper_analyses, ensure_ascii=False)}
"""

        print("Sent paper analyses to model for cross-paper synthesis.")
        synthesis = _invoke_pdf(
            llm, None, synthesis_prompt, model_name, price_table,
            "hypothesis_synthesis", inference_history, api_usage,
        )

        if synthesis is not None:
            print("Tailoring final output through critique and refinement.")
            critique_prompt = f"""
Critically review and refine this draft for topic: {topic}
Additional instructions: {additional_prompt or 'None'}
Check unsupported claims, vague/non-falsifiable hypotheses, duplicates, hidden assumptions,
and restatements of known findings. Return ONLY valid JSON with keys historical_analysis,
research_gaps (list of strings), and hypotheses (list of objects containing hypothesis,
rationale, supporting_papers, testable_prediction, caveats). Keep it concise and evidence-grounded.
Do not claim novelty beyond the supplied papers.
DRAFT:
{synthesis}
"""

            final_raw = _invoke_pdf(
                llm, None, critique_prompt, model_name, price_table,
                "self_critique_refinement", inference_history, api_usage,
            )

            if final_raw is not None:
                parsed = _parse_final_output(final_raw)
            else:
                parsed = _parse_final_output(synthesis)
                parsed["critique_warning"] = (
                    "Critique request failed; showing synthesis output."
                )
        else:
            parsed["synthesis_warning"] = "Synthesis request failed."
    else:
        parsed["analysis_warning"] = "No papers were successfully analysed."

    parsed["hypotheses"] = deduplicate_hypotheses(parsed.get("hypotheses", []))

    successful = [item for item in api_usage if item["status"] == "success"]
    costs = [
        item["estimated_cost_usd"]
        for item in successful
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
        "stage": "final_result",
        "status": "success",
        "result": parsed,
    })

    return {
        "agent_params": {
            "mode": "single",
            "topic": topic,
            "additional_prompt": additional_prompt,
            "model": model_name,
            "pause_sec": pause_sec,
            "papers": [str(path) for path in pdf_paths],
        },
        "paper_analyses": paper_analyses,
        "historical_analysis": parsed.get("historical_analysis", ""),
        "research_gaps": parsed.get("research_gaps", []),
        "hypotheses": parsed.get("hypotheses", []),
        "parse_warning": parsed.get("parse_warning"),
        "usage_summary": usage_summary,
        "api_usage": api_usage,
        "inference_history": inference_history,
    }
