"""Single-LLM paper analysis and hypothesis-generation pipeline."""

from pathlib import Path
from pypdf import PdfReader
import json
import time
from datetime import datetime, timezone


def extract_pdf_text(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()

    if not text:
        print(f"[WARNING] No text extracted from {pdf_path}. Skipping this PDF.")
        return None

    return text


def _usage_from_response(response):
    """Read token usage exposed by LangChain; absent fields remain None."""
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens


def _log_usage(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _invoke(llm, prompt, model_name, usage_log_path, price_table, stage, paper=None):
    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        response = llm.invoke(prompt)
        runtime_seconds = round(time.perf_counter() - start, 3)
        input_tokens, output_tokens, total_tokens = _usage_from_response(response)

        prices = price_table or {}
        input_rate = prices.get("input")
        output_rate = prices.get("output")
        estimated_cost_usd = None
        if input_tokens is not None and output_tokens is not None:
            if input_rate is not None and output_rate is not None:
                estimated_cost_usd = (
                    input_tokens * input_rate + output_tokens * output_rate
                ) / 1_000_000

        record = {
            "timestamp_utc": timestamp,
            "stage": stage,
            "paper": paper,
            "model": model_name,
            "status": "success",
            "runtime_seconds": runtime_seconds,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "error": None,
        }
        _log_usage(usage_log_path, record)
        return response.content, record
    except Exception as exc:
        runtime_seconds = round(time.perf_counter() - start, 3)
        _log_usage(usage_log_path, {
            "timestamp_utc": timestamp,
            "stage": stage,
            "paper": paper,
            "model": model_name,
            "status": "error",
            "runtime_seconds": runtime_seconds,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
            "error": f"{type(exc).__name__}: {exc}",
        })
        raise


def deduplicate_hypotheses(hypotheses):
    """
    Placeholder for future local cosine-similarity filtering.
    Currently returns the hypotheses unchanged.
    """
    return hypotheses


def run_single_agent(
    llm,
    topic,
    additional_prompt,
    pdf_paths,
    model_name,
    usage_log_path,
    price_per_million_tokens=None,
):
    price_table = price_per_million_tokens or {}
    paper_analyses = []
    usage_records = []
    total_start = time.perf_counter()

    # Stage 1: analyze each paper separately to preserve paper-level context.
    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        paper_text = extract_pdf_text(pdf_path)
        if not paper_text:
            continue
        prompt = f"""
You are assisting with scientific hypothesis generation.

Research topic: {topic}
Additional user instructions: {additional_prompt or "None"}
Paper filename: {pdf_path.name}

Analyze ONLY the paper text below. Do not invent facts. Distinguish what the
paper explicitly reports from your own interpretation. Return:
1. Context and central research question
2. Methods and key findings
3. Limitations or unresolved questions
4. Potential research gaps relevant to the topic
5. Candidate scientific hypotheses grounded in this paper
6. Useful evidence/quotes or section references, if available

PAPER TEXT:
{paper_text}
"""
        content, usage = _invoke(
            llm, prompt, model_name, usage_log_path, price_table,
            stage="paper_analysis", paper=pdf_path.name
        )
        paper_analyses.append({
            "paper": pdf_path.name,
            "analysis": content,
        })
        usage_records.append(usage)
        print(f"Analyzed: {pdf_path.name}")

    # Stage 2: synthesize candidate hypotheses across papers.
    synthesis_prompt = f"""
You are a careful scientific research assistant.

Research topic: {topic}
Additional user instructions: {additional_prompt or "None"}

Below are separate analyses of papers. Use only the supplied evidence and
clearly mark speculative claims. Identify:
1. A concise analysis of how the research area has developed across the papers
2. The strongest research gaps, with supporting paper filenames
3. Candidate hypotheses that are specific, falsifiable, scientifically useful,
   and testable in principle
4. For each hypothesis: rationale, supporting papers, assumptions, and a
   possible way to test it
5. Important caveats and evidence that could contradict each hypothesis

PAPER ANALYSES:
{json.dumps(paper_analyses, ensure_ascii=False)}
"""
    synthesis, usage = _invoke(
        llm, synthesis_prompt, model_name, usage_log_path, price_table,
        stage="hypothesis_synthesis"
    )
    usage_records.append(usage)

    # Stage 3: self-critique and refinement.
    critique_prompt = f"""
Critically review the following draft scientific research analysis.

Research topic: {topic}
Additional user instructions: {additional_prompt or "None"}

Identify unsupported claims, vague or non-falsifiable hypotheses, duplicates,
hidden assumptions, and hypotheses that merely restate known findings.
Then provide a refined final version with:
- historical analysis of the supplied papers
- research gaps
- a final, numbered hypothesis set
- rationale, supporting paper filenames, and a testable prediction for each
- caveats and confidence limitations

Do not claim that a hypothesis is novel beyond the supplied papers; state that
a broader literature search would be needed to establish novelty.

DRAFT:
{synthesis}
"""
    final_text, usage = _invoke(
        llm, critique_prompt, model_name, usage_log_path, price_table,
        stage="self_critique_refinement"
    )
    usage_records.append(usage)

    # Placeholder for local semantic similarity deduplication.
    # For now, preserve the model's final output unchanged.
    hypotheses = deduplicate_hypotheses([final_text])

    successful = [r for r in usage_records if r["status"] == "success"]
    input_sum = sum(r["input_tokens"] or 0 for r in successful)
    output_sum = sum(r["output_tokens"] or 0 for r in successful)
    total_sum = sum(r["total_tokens"] or 0 for r in successful)
    known_costs = [
        r["estimated_cost_usd"] for r in successful
        if r["estimated_cost_usd"] is not None
    ]

    return {
        "agent_params": {
            "mode": "single",
            "topic": topic,
            "additional_prompt": additional_prompt,
            "model": model_name,
            "papers": [str(p) for p in pdf_paths],
        },
        "paper_analyses": paper_analyses,
        "research_gaps_and_hypotheses": hypotheses,
        "usage_summary": {
            "api_calls_logged": len(usage_records),
            "successful_calls": len(successful),
            "failed_calls": len(usage_records) - len(successful),
            "input_tokens": input_sum,
            "output_tokens": output_sum,
            "total_tokens": total_sum,
            "estimated_cost_usd": round(sum(known_costs), 8) if known_costs else None,
            "cost_note": (
                "Cost is None unless per-million-token prices are configured "
                "in main.py. Token usage and runtime are logged per call."
            ),
            "total_runtime_seconds": round(time.perf_counter() - total_start, 3),
            "usage_log": str(usage_log_path),
        },
    }
