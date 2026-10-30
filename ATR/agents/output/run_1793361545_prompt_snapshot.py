def run_multi_debate(
    llm, topic, additional_prompt, pdf_paths, model_name,
    price_per_million_tokens=None,
):
    """
    Multi-agent entry point matching main.py's single-agent input contract.
    Returns separate research gaps/hypotheses, full provenance, usage and logs.
    Does not write files; main.py owns all output writing.
    """
    global _last_request_completed_at
    _last_request_completed_at = None

    if not topic or not str(topic).strip():
        raise ValueError("topic cannot be empty.")
    pdf_paths = [Path(p) for p in pdf_paths]
    if not pdf_paths:
        raise ValueError("pdf_paths must contain at least one PDF.")

    prices = price_per_million_tokens or {}
    started = time.perf_counter()
    history, api_usage, paper_analyses = [], [], []

    # Google Search grounding is used only by the external literature verifier.
    search_llm = None
    try:
        search_llm = llm.bind_tools([{"google_search": {}}])
        print("[WEB] Google Search grounding enabled.")
    except Exception as exc:
        print(f"[WEB WARNING] Google Search grounding unavailable: {exc}")

    # 1. Each PDF is read independently; requests are sequential.
    print(f"[MULTI] Analysing {len(pdf_paths)} papers sequentially.")
    for index, paper in enumerate(pdf_paths, start=1):
        print(f"[PAPER] {paper.name} ({index}/{len(pdf_paths)}).")
        result = _call(
            llm, _reader_prompt(topic, additional_prompt, paper),
            stage="paper_analysis", agent="Literature Analyst",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, paper=paper,
        )
        if result is None:
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": "paper_analysis_skipped", "agent": "Orchestrator",
                "paper": str(paper.resolve()), "status": "warning",
                "message": "Paper request failed; excluded from synthesis.",
            })
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        paper_analyses.append({
            "paper": str(paper.resolve()), "paper_filename": paper.name,
            "analysis": parsed if parsed is not None else raw,
        })
        print(f"[PAPER] Completed {paper.name}.")

    if not paper_analyses:
        raise RuntimeError("No paper could be analysed successfully.")

    # 2. Four independent perspectives identify research gaps.
    gap_candidates = []
    for perspective in PERSPECTIVES:
        print(f"[GAPS] {perspective.title()} perspective.")
        result = _call(
            llm, _perspective_prompt(
                topic, additional_prompt, perspective, paper_analyses
            ),
            stage="research_gap_generation",
            agent=f"{perspective.title()} Gap Analyst",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage,
        )
        if result is None:
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        if parsed:
            items = _assign_ids(parsed.get("research_gaps", []), "G", perspective)
            gap_candidates.extend(items)
            history[-1]["action_summary"] = (
                f"Independently proposed {len(items)} research gap(s)."
            )

    # 3. Search external literature to verify candidate gaps.
    gap_verification, gap_web_sources = {}, []
    if gap_candidates:
        print("[WEB] Verifying research gaps against external literature.")
        result = _call(
            llm, _verify_prompt(topic, gap_candidates, "research gaps"),
            stage="research_gap_web_verification",
            agent="External Literature Verification Agent",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, use_search=True, search_llm=search_llm,
        )
        if result is not None:
            raw, gap_web_sources = result
            gap_verification = _parsed_event(history, raw) or {}
        _apply_verification(gap_candidates, gap_verification, gap_web_sources)

    # 4. Debate and adjudicate gaps for three rounds.
    active_gaps, rejected_gaps, gap_debate = _run_debate(
        llm, topic, "research_gap", gap_candidates, gap_verification,
        model_name, prices, history, api_usage,
    )

    # 5. Four independent perspectives generate hypotheses from surviving gaps.
    hypothesis_candidates = []
    for perspective in PERSPECTIVES:
        if not active_gaps:
            break
        print(f"[HYPOTHESES] {perspective.title()} perspective.")
        result = _call(
            llm, _hypothesis_prompt(
                topic, additional_prompt, perspective, active_gaps, paper_analyses
            ),
            stage="hypothesis_generation",
            agent=f"{perspective.title()} Hypothesis Generator",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage,
        )
        if result is None:
            continue
        raw, _ = result
        parsed = _parsed_event(history, raw)
        if parsed:
            items = _assign_ids(parsed.get("hypotheses", []), "H", perspective)
            hypothesis_candidates.extend(items)
            history[-1]["action_summary"] = (
                f"Independently proposed {len(items)} hypothesis/hypotheses."
            )

    # 6. External literature verification for hypotheses.
    hypothesis_verification, hypothesis_web_sources = {}, []
    if hypothesis_candidates:
        print("[WEB] Verifying hypotheses against external literature.")
        result = _call(
            llm, _verify_prompt(
                topic, hypothesis_candidates, "candidate hypotheses"
            ),
            stage="hypothesis_web_verification",
            agent="External Literature Verification Agent",
            model_name=model_name, prices=prices, history=history,
            usage_log=api_usage, use_search=True, search_llm=search_llm,
        )
        if result is not None:
            raw, hypothesis_web_sources = result
            hypothesis_verification = _parsed_event(history, raw) or {}
        _apply_verification(
            hypothesis_candidates, hypothesis_verification, hypothesis_web_sources
        )

    # 7. Debate and adjudicate hypotheses for three rounds.
    active_hypotheses, rejected_hypotheses, hypothesis_debate = _run_debate(
        llm, topic, "hypothesis", hypothesis_candidates,
        hypothesis_verification, model_name, prices, history, api_usage,
    )

    # 8. Final curator keeps gaps and hypotheses as separate ranked lists.
    print("[FINAL] Curating separate research-gap and hypothesis lists.")
    result = _call(
        llm, _curator_prompt(
            topic, active_gaps, active_hypotheses,
            rejected_gaps, rejected_hypotheses,
        ),
        stage="final_curation", agent="Final Scientific Curator",
        model_name=model_name, prices=prices, history=history,
        usage_log=api_usage,
    )
    final_data = {}
    if result is not None:
        raw, _ = result
        final_data = _parsed_event(history, raw) or {}

    final_gaps = final_data.get("research_gaps") or active_gaps
    final_hypotheses = final_data.get("hypotheses") or active_hypotheses
    historical_analysis = final_data.get("historical_analysis", "")

    successful = [x for x in api_usage if x["status"] == "success"]
    costs = [
        x["estimated_cost_usd"] for x in successful
        if x["estimated_cost_usd"] is not None
    ]
    usage_summary = {
        "api_calls_logged": len(api_usage),
        "successful_calls": len(successful),
        "failed_calls": len(api_usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "note": "Usage covers calls recorded by this pipeline, not account-wide quota.",
    }

    history.append({
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": "final_result", "agent": "Orchestrator", "status": "success",
        "message": (
            f"Final output: {len(final_gaps)} research gap(s), "
            f"{len(final_hypotheses)} hypothesis/hypotheses."
        ),
    })
    history_text = _format_history(topic, history)

    return {
        "agent_params": {
            "mode": "multi_debate",
            "topic": topic,
            "additional_prompt": additional_prompt,
            "model": model_name,
            "papers": [str(p.resolve()) for p in pdf_paths],
            "perspectives": list(PERSPECTIVES),
            "debate_rounds": DEBATE_ROUNDS,
            "execution": "sequential independent agent calls; no concurrent requests",
            "pause_after_response_seconds": PAUSE_SEC,
        },
        "paper_analyses": paper_analyses,
        "historical_analysis": historical_analysis,
        "research_gaps": [_format_gap(x) for x in final_gaps],
        "research_gap_records": final_gaps,
        "hypotheses": final_hypotheses,
        "rejected_research_gaps": rejected_gaps,
        "rejected_hypotheses": rejected_hypotheses,
        "debate_summaries": {
            "research_gaps": gap_debate,
            "hypotheses": hypothesis_debate,
        },
        "web_verification": {
            "research_gaps": gap_verification,
            "hypotheses": hypothesis_verification,
        },
        "usage_summary": usage_summary,
        "api_usage": api_usage,
        "inference_history": history,
        "inference_history_text": history_text,
    }
