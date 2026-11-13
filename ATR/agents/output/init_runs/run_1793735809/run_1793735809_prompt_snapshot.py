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
