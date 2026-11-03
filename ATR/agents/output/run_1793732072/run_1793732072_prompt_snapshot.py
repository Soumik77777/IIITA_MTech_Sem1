def run_multi_debate(llm, topic, additional_prompt, pdf_paths, model_name,
                     price_per_million_tokens=None):
    """Existing main.py-compatible entry point; returns data and logs only."""
    global _last_request_completed_at
    _last_request_completed_at = None
    if not topic or not str(topic).strip():
        raise ValueError("topic cannot be empty.")
    paths = [Path(p).resolve() for p in pdf_paths]
    if not paths:
        raise ValueError("pdf_paths must contain at least one PDF.")
    prices = price_per_million_tokens or {}
    started = time.perf_counter()
    history, usage, papers = [], [], []

    # 1. Reader: one independent call per paper.
    print(f"[READER] Reading {len(paths)} papers sequentially.")
    for index, path in enumerate(paths, 1):
        pid = f"P{index:03d}"
        parsed = _call(
            llm, _reader_prompt(topic, additional_prompt, pid, path),
            stage="paper_reading", agent="Literature Reader",
            model_name=model_name, prices=prices, history=history,
            usage_log=usage, paper_path=path,
        )
        if not isinstance(parsed, dict):
            history.append({
                "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
                "stage": "paper_reading_skipped", "agent": "Orchestrator",
                "paper_id": pid, "paper_loc": str(path), "status": "warning",
                "message": "Paper failed or returned invalid JSON.",
            })
            continue
        papers.append({"paper_id": pid, "paper_loc": str(path),
                       "paper_filename": path.name, "analysis": parsed})
    if not papers:
        raise RuntimeError("No paper could be read successfully.")
    cards = _paper_cards(papers)
    valid_ids = {x["paper_id"] for x in cards}

    # 2. Topic-adaptive perspective finder.
    print("[PERSPECTIVES] Discovering topic-specific perspectives.")
    perspective_data = _call(
        llm, _finder_prompt(topic, additional_prompt, cards),
        stage="perspective_discovery", agent="Topic-Adaptive Perspective Finder",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
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
        print(f"[GAPS] {perspective['name']}")
        parsed = _call(
            llm, _gap_prompt(topic, additional_prompt, perspective, cards),
            stage="research_gap_generation",
            agent=f"{perspective['name']} Gap Generator",
            model_name=model_name, prices=prices, history=history, usage_log=usage,
        ) or {}
        new, next_id = _new_records(
            parsed.get("research_gaps", []), "G", next_id,
            perspective["name"], valid_ids)
        candidates.extend(new)

    # 4. Curator/analyser checks every candidate against every paper card.
    print("[CURATOR] Curating gaps and checking the complete corpus.")
    curated = _call(
        llm, _curator_prompt(topic, candidates, cards),
        stage="initial_gap_curation_and_corpus_analysis",
        agent="Research-Gap Curator and Corpus Analyser",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
    ) or {}
    gaps, rejected_gaps = _apply_initial_curation(candidates, curated, valid_ids, history)

    # 5. Gap debate.
    gaps, debate_rejected, gap_rounds = _run_debate(
        llm, topic, "research_gap", gaps, perspectives, cards,
        model_name, prices, history, usage, valid_ids)
    rejected_gaps.extend(debate_rejected)

    # 6. Hypothesis generation: one call per perspective, IDs global.
    hypotheses, next_hid = [], 1
    if gaps:
        for perspective in perspectives:
            print(f"[HYPOTHESES] {perspective['name']}")
            parsed = _call(
                llm, _hypothesis_prompt(topic, additional_prompt, perspective, gaps, cards),
                stage="hypothesis_generation",
                agent=f"{perspective['name']} Hypothesis Generator",
                model_name=model_name, prices=prices, history=history, usage_log=usage,
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
        llm, topic, "hypothesis", hypotheses, perspectives, cards,
        model_name, prices, history, usage, valid_ids)

    # 8. Final curation. Fail-safe preserves IDs and records omitted by curator.
    final_data = _call(
        llm, _final_prompt(topic, gaps, hypotheses),
        stage="final_curation", agent="Final Output Curator",
        model_name=model_name, prices=prices, history=history, usage_log=usage,
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

    successful = [x for x in usage if x["status"] == "success"]
    costs = [x["estimated_cost_usd"] for x in successful
             if x["estimated_cost_usd"] is not None]
    summary = {
        "api_calls_logged": len(usage), "successful_calls": len(successful),
        "failed_calls": len(usage) - len(successful),
        "input_tokens": sum(x["input_tokens"] or 0 for x in successful),
        "output_tokens": sum(x["output_tokens"] or 0 for x in successful),
        "total_tokens": sum(x["total_tokens"] or 0 for x in successful),
        "estimated_cost_usd": round(sum(costs), 8) if costs else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "note": "Pipeline usage only; not account-wide quota.",
    }
    history.append({
        "event_id": f"E{len(history)+1:04d}", "timestamp_utc": _now(),
        "stage": "final_result", "agent": "Orchestrator", "status": "success",
        "message": f"{len(final_gaps)} gaps and {len(final_hypotheses)} hypotheses.",
    })
    return {
        "agent_params": {
            "mode": "adaptive_multi_agent", "topic": topic,
            "additional_prompt": additional_prompt, "model": model_name,
            "papers": [{"paper_id": p["paper_id"], "paper_loc": p["paper_loc"]}
                       for p in papers],
            "perspectives": perspectives, "debate_rounds_max": DEBATE_ROUNDS,
            "debate_termination": "Stop when challenger proposes no changes.",
            "execution": "Sequential API calls; no concurrent requests.",
            "pause_after_response_seconds": PAUSE_SEC, "web_search": False,
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
        "usage_summary": summary, "api_usage": usage,
        "inference_history": history,
        "inference_history_text": _history_text(topic, history),
    }
