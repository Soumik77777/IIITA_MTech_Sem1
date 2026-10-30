def run_single_agent(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    price_table = price_per_million_tokens or {}
    inference_history, api_usage, paper_analyses = [], [], []
    total_start = time.perf_counter()

    # Each PDF is sent in its own sequential request, not as one combined batch.
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
        if content is None:
            print(f"[WARNING] Skipping failed paper request: {pdf_path.name}")
            inference_history.append({"stage": "paper_analysis_skipped", "paper": pdf_path.name,
                                      "message": "No analysis generated for this paper."})
            continue
        paper_analyses.append({"paper": pdf_path.name, "analysis": content})
        print(f"Analyzed: {pdf_path.name}")
        inference_history.append({"stage": "paper_analysis_log", "paper": pdf_path.name,
                                  "message": f"Analyzed: {pdf_path.name}"})

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
        if synthesis is not None:
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
            if final_raw is not None:
                parsed = _parse_final_output(final_raw)
            else:
                parsed = _parse_final_output(synthesis)
                parsed["critique_warning"] = "Critique request failed; showing synthesis output."
        else:
            parsed["synthesis_warning"] = "Synthesis request failed."

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
