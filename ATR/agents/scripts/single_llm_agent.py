"""Single-LLM PDF analysis pipeline. Returns logs to main.py; writes no files."""

from pathlib import Path
from pypdf import PdfReader
import base64
import json
import time
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage


def extract_pdf_text(pdf_path: Path):
    """Optional legacy helper; the agent submits PDFs directly instead."""
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if not text:
        print(f"[WARNING] No text extracted from {pdf_path}.")
        return None
    return text


def _usage_from_response(response):
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens


def _invoke_pdf(llm, pdf_path, prompt, model_name, price_table, stage,
                inference_history, api_usage, paper=None):
    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    event = {"timestamp_utc": timestamp, "stage": stage, "paper": paper,
             "prompt": prompt, "status": "started"}
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
        response = llm.invoke([message])
        runtime = round(time.perf_counter() - start, 3)
        in_tokens, out_tokens, total_tokens = _usage_from_response(response)
        prices = price_table or {}
        cost = None
        if in_tokens is not None and out_tokens is not None:
            if prices.get("input") is not None and prices.get("output") is not None:
                cost = (in_tokens * prices["input"] + out_tokens * prices["output"]) / 1_000_000
        api_usage.append({
            "timestamp_utc": timestamp, "stage": stage, "paper": paper,
            "model": model_name, "status": "success", "runtime_seconds": runtime,
            "input_tokens": in_tokens, "output_tokens": out_tokens,
            "total_tokens": total_tokens, "estimated_cost_usd": cost, "error": None,
        })
        event.update({"status": "success", "response": response.content,
                      "runtime_seconds": runtime})
        content = response.content
        if isinstance(content, list):
            content = "\n".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        return content
    except Exception as exc:
        runtime = round(time.perf_counter() - start, 3)
        api_usage.append({
            "timestamp_utc": timestamp, "stage": stage, "paper": paper,
            "model": model_name, "status": "error", "runtime_seconds": runtime,
            "input_tokens": None, "output_tokens": None, "total_tokens": None,
            "estimated_cost_usd": None, "error": f"{type(exc).__name__}: {exc}",
        })
        event.update({"status": "error", "error": f"{type(exc).__name__}: {exc}",
                      "runtime_seconds": runtime})
        raise


def deduplicate_hypotheses(hypotheses):
    """Placeholder for future local cosine-similarity filtering."""
    return hypotheses


def _parse_final_output(text):
    if isinstance(text, list):
        text = "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in text
        )
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
    return {"historical_analysis": text, "research_gaps": [], "hypotheses": [],
            "parse_warning": "Model response was not valid JSON; raw response is in inference_history."}


def run_single_agent(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    price_table = price_per_million_tokens or {}
    inference_history, api_usage, paper_analyses = [], [], []
    total_start = time.perf_counter()

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
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
        content = _invoke_pdf(llm, pdf_path, prompt, model_name, price_table,
                              "paper_analysis", inference_history, api_usage, pdf_path.name)
        paper_analyses.append({"paper": pdf_path.name, "analysis": content})
        print(f"Analyzed: {pdf_path.name}")
        inference_history.append({"stage": "paper_analysis_log", "paper": pdf_path.name,
                                  "message": f"Analyzed: {pdf_path.name}"})

    synthesis_prompt = f"""
Synthesize the following paper-level analyses for the topic: {topic}
Additional instructions: {additional_prompt or 'None'}
Use only supplied evidence; distinguish speculation. Return ONLY valid JSON, no Markdown,
with exactly this structure:
{{
  "historical_analysis": "Concise account of how the research area developed",
  "research_gaps": ["Specific gap with supporting paper filenames"],
  "hypotheses": [{{"hypothesis":"Specific, falsifiable hypothesis",
    "rationale":"Evidence-based rationale", "supporting_papers":["paper.pdf"],
    "testable_prediction":"Possible test", "caveats":"Assumptions or counterevidence"}}]
}}
Do not claim novelty beyond these papers; broader literature review is required to establish novelty.
PAPER ANALYSES:
{json.dumps(paper_analyses, ensure_ascii=False)}
"""
    synthesis = _invoke_pdf(llm, None, synthesis_prompt, model_name, price_table,
                            "hypothesis_synthesis", inference_history, api_usage)

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
    final_raw = _invoke_pdf(llm, None, critique_prompt, model_name, price_table,
                            "self_critique_refinement", inference_history, api_usage)
    parsed = _parse_final_output(final_raw)
    parsed["hypotheses"] = deduplicate_hypotheses(parsed.get("hypotheses", []))

    successful = [x for x in api_usage if x["status"] == "success"]
    costs = [x["estimated_cost_usd"] for x in successful if x["estimated_cost_usd"] is not None]
    usage_summary = {
        "api_calls_logged": len(api_usage), "successful_calls": len(successful),
        "failed_calls": len(api_usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - total_start, 3),
    }
    inference_history.append({"stage": "final_result", "status": "success", "result": parsed})
    return {
        "agent_params": {"mode": "single", "topic": topic,
                         "additional_prompt": additional_prompt, "model": model_name,
                         "papers": [str(p) for p in pdf_paths]},
        "paper_analyses": paper_analyses,
        "historical_analysis": parsed.get("historical_analysis", ""),
        "research_gaps": parsed.get("research_gaps", []),
        "hypotheses": parsed.get("hypotheses", []),
        "parse_warning": parsed.get("parse_warning"),
        "usage_summary": usage_summary,
        "api_usage": api_usage,
        "inference_history": inference_history,
    }
