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
