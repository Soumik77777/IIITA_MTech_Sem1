#!/usr/bin/env python3
"""Build run/dataset/architecture mappings and blank LLM-evaluation CSVs.

Configure RUN_FOLDERS and ANALYSIS_OUTPUT_FOLDER below, then run:
    python evaluate_runs.py

The script reads run artifacts only. It does not modify the source run folders.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EVALUATORS = ["GPT", "Gemini", "Claude", "Grok", "DeepSeek"]
SCORE_DIMENSIONS = ["Novelty", "Significance", "Feasibility", "Testability"]

# Add the run output folders to analyse, in order you want for R01, R02, ...
RUN_FOLDERS = [
    Path("ATR/agents/output/run_1794660685"),
    Path("ATR/agents/output/run_1794662507"),
    Path("ATR/agents/output/run_1794668371"),
    Path("ATR/agents/output/run_1794670582"),
    Path("ATR/agents/output/run_1794671050"),
    Path("ATR/agents/output/run_1794672027"),
    Path("ATR/agents/output/run_1794672429"),
    Path("ATR/agents/output/run_1794679494"),
    Path("ATR/agents/output/run_1794723348"),
    Path("ATR/agents/output/run_1794725368"),
    Path("ATR/agents/output/run_1794725720"),
    Path("ATR/agents/output/run_1794727099"),
    Path("ATR/agents/output/run_1794729254"),
    Path("ATR/agents/output/run_1794730841"),
]

# All five CSV files will be written here.
ANALYSIS_OUTPUT_FOLDER = Path("ATR/agents/analysis")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARNING] Could not read {path.name}: {exc}")
        return None


def find_artifact(run_dir: Path, suffix: str) -> Path | None:
    """Find an artifact by its run-specific suffix, with a generic fallback."""
    run_id = run_dir.name.removeprefix("run_")
    candidates = [
        run_dir / f"run_{run_id}_{suffix}",
        run_dir / suffix,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = sorted(run_dir.glob(f"*_{suffix}"))
    return matches[0] if matches else None


def normalise_path(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("paper_loc") or value.get("path") or value.get("file")
    if value is None:
        return ""
    return str(value)


def extract_paper_paths(history: dict[str, Any]) -> list[str]:
    params = history.get("agent_params") or {}
    papers = params.get("papers") or []
    paths = [normalise_path(p) for p in papers]
    paths = [p for p in paths if p]

    if not paths:
        final = history.get("final_result") or {}
        analyses = final.get("paper_analyses") or []
        for paper in analyses:
            p = normalise_path(paper)
            if p:
                paths.append(p)

    if not paths:
        events = history.get("events") or history.get("inference_history") or []
        for event in events:
            if event.get("stage") in {"paper_analysis", "paper_analysis_log"}:
                p = normalise_path(event.get("paper_loc") or event.get("paper"))
                if p:
                    paths.append(p)

    # Preserve the original path strings for the mapping table, but sort for
    # stable dataset identity regardless of paper ordering in a run.
    return sorted(dict.fromkeys(paths), key=lambda x: x.lower())


def dataset_fingerprint(paper_paths: list[str]) -> str:
    # Use normalized absolute paths when possible; the displayed mapping keeps
    # the original source paths. This avoids assigning different IDs just
    # because the input list order differed.
    canonical = []
    for p in paper_paths:
        try:
            canonical.append(str(Path(p).expanduser().resolve()))
        except OSError:
            canonical.append(p)
    payload = "\n".join(sorted(canonical, key=str.lower))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def extract_items(history: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    final = history.get("final_result") or {}

    # Some versions put the final result directly at the root.
    if not final:
        final = history

    gaps_raw = final.get("research_gap_records")
    if not isinstance(gaps_raw, list) or not gaps_raw:
        gaps_raw = final.get("research_gaps") or []

    hypotheses_raw = final.get("hypotheses") or []

    def item_text(item: Any, keys: tuple[str, ...]) -> str:
        if isinstance(item, dict):
            for key in keys:
                value = item.get(key)
                if value:
                    return str(value)
            return json.dumps(item, ensure_ascii=False)
        return str(item)

    gaps: list[dict[str, str]] = []
    for i, item in enumerate(gaps_raw, start=1):
        if isinstance(item, dict):
            item_id = str(item.get("id") or f"G{i:03d}")
        else:
            # Existing single-agent text outputs often begin with G001:.
            match = re.match(r"^\s*(G\d+)\s*:", str(item))
            item_id = match.group(1) if match else f"G{i:03d}"
        gaps.append({
            "item_id": item_id,
            "item_type": "Research Gap",
            "item_text": item_text(item, ("gap", "research_gap", "description")),
        })

    hypotheses: list[dict[str, str]] = []
    for i, item in enumerate(hypotheses_raw, start=1):
        item_id = str(item.get("id") or f"H{i:03d}") if isinstance(item, dict) else f"H{i:03d}"
        hypotheses.append({
            "item_id": item_id,
            "item_type": "Hypothesis",
            "item_text": item_text(item, ("hypothesis", "statement", "description")),
        })

    return gaps, hypotheses


def extract_mode(params: dict[str, Any], run_dir: Path) -> str:
    mode = str(params.get("mode") or "").strip().lower()
    if mode in {"single", "multi"}:
        return mode
    snapshot_name = " ".join(p.name.lower() for p in run_dir.glob("*prompt_snapshot*.py"))
    if "multi" in snapshot_name or "debate" in snapshot_name:
        return "multi"
    if "single" in snapshot_name:
        return "single"
    return ""


def extract_model(params: dict[str, Any], usage: dict[str, Any], history: dict[str, Any]) -> str:
    model = params.get("model") or usage.get("model") or history.get("model")
    if not model:
        calls = usage.get("calls") or []
        model = next((c.get("model") for c in calls if c.get("model")), "")
    return str(model or "")


def extract_llm_params(params: dict[str, Any], usage: dict[str, Any]) -> str:
    """Return the LLM parameters actually applied, as a JSON dict; absent values are NA.

    Only temperature for now. To track another model's parameters, add keys to the dict.
    """
    temperature = "NA"

    for source in (params, usage):
        if not isinstance(source, dict):
            continue
        if temperature == "NA" and source.get("temperature_applied"):
            value = source.get("temperature_requested")
            if value is not None:
                temperature = value
        for parent_key in ("generation_config", "model_params", "llm_params"):
            nested = source.get(parent_key)
            if isinstance(nested, dict) and temperature == "NA" and nested.get("temperature") is not None:
                temperature = nested["temperature"]

    return json.dumps({"temperature": temperature}, ensure_ascii=False, sort_keys=True)


def extract_max_rounds(params: dict[str, Any], mode: str) -> Any:
    """Maximum critique rounds (single) or debate rounds (multi); NA if not recorded.

    Single stores its limit in self_critique_rounds (its debate_rounds_max is always 0);
    multi stores it in debate_rounds_max. A value of 0 is treated as "not applicable".
    """
    keys = ("self_critique_rounds", "debate_rounds_max") if mode == "single" \
        else ("debate_rounds_max", "self_critique_rounds")
    for key in keys:
        value = params.get(key)
        if value not in (None, 0):
            return value
    return "NA"


def count_txt_items(path: Path | None, prefix: str) -> int | None:
    """Count '- G001: ...' / '- H001: ...' entries written by main.py."""
    if path is None or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return len(re.findall(rf"^- {prefix}\d+:", text, flags=re.MULTILINE))


def extract_metrics(history: dict[str, Any], usage_data: dict[str, Any]) -> dict[str, Any]:
    final = history.get("final_result") or {}
    summary = usage_data.get("usage_summary") or final.get("usage_summary") or {}
    calls = usage_data.get("calls") or final.get("api_usage") or []

    successful_calls = [c for c in calls if str(c.get("status", "")).lower() in {"success", "succeeded"}]
    failed_calls = [c for c in calls if str(c.get("status", "")).lower() in {"error", "failed"}]

    def total(field: str) -> int:
        value = summary.get(field)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
        return sum(int(c.get(field) or 0) for c in successful_calls)

    runtime = summary.get("total_runtime_seconds")
    if runtime is None:
        runtime = summary.get("runtime_seconds")
    if runtime is None:
        runtime = sum(float(c.get("runtime_seconds") or 0) for c in calls)

    params = history.get("agent_params") or final.get("agent_params") or {}
    pause_seconds = ""
    for source in (params, usage_data, summary):
        if not isinstance(source, dict):
            continue
        for key in ("pause_after_response_seconds", "pause_between_calls_seconds", "pause_seconds", "pause_sec"):
            if source.get(key) is not None:
                pause_seconds = source[key]
                break
        if pause_seconds != "":
            break

    return {
        "api_calls": summary.get("api_calls_logged", len(calls)),
        "failed_calls": summary.get("failed_calls", len(failed_calls)),
        "runtime_seconds": runtime if runtime is not None else "",
        "pause_between_calls_seconds": pause_seconds,
        "input_tokens": total("input_tokens"),
        "output_tokens": total("output_tokens"),
        "total_tokens": total("total_tokens"),
    }


def write_csv(path: Path, rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def build_score_rows(run_records: list[dict[str, Any]]) -> list[list[Any]]:
    fixed_headers = ["Run ID", "Gap/Hypothesis ID", "Item Type", "Item Text"]
    header_1: list[Any] = fixed_headers.copy()
    header_2: list[Any] = ["", "", "", ""]

    for dimension in SCORE_DIMENSIONS:
        header_1.extend([f"{dimension} Score"] + [""] * (len(EVALUATORS) - 1))
        header_2.extend(EVALUATORS)

    rows: list[list[Any]] = [header_1, header_2]
    for record in run_records:
        for item in record["items"]:
            # Score cells intentionally empty for manual LLM evaluation.
            rows.append([
                record["human_run_id"], item["item_id"],
                item["item_type"], item["item_text"],
                *([""] * (len(SCORE_DIMENSIONS) * len(EVALUATORS))),
            ])
    return rows


def main() -> None:
    run_dirs = [Path(p).expanduser().resolve() for p in RUN_FOLDERS]
    analysis_dir = Path(ANALYSIS_OUTPUT_FOLDER).expanduser().resolve()
    analysis_dir.mkdir(parents=True, exist_ok=True)

    run_mapping: list[list[Any]] = [["Original Run ID", "Human-readable Run ID"]]
    dataset_mapping: list[list[Any]] = [["Dataset ID", "Paper Count", "Paper Paths"]]
    architecture_mapping: list[list[Any]] = [["Architecture ID", "Mode", "Prompt Snapshot"]]
    metadata_rows: list[list[Any]] = [[
        "Run ID", "Dataset ID", "Mode", "LLM Model", "LLM Parameters",
        "Architecture ID", "Max Rounds", "Total API Calls", "Failed Calls", "Input Tokens", "Output Tokens",
        "Total Tokens", "Runtime (seconds)", "Pause Between Calls (seconds)",
        "Total Gaps", "Total Hypotheses",
    ]]

    dataset_ids: dict[str, str] = {}
    architecture_ids: dict[str, str] = {}
    run_records: list[dict[str, Any]] = []

    for run_index, run_dir in enumerate(run_dirs, start=1):
        if not run_dir.is_dir():
            print(f"[WARNING] Run folder not found; skipping: {run_dir}")
            continue

        original_run_id = run_dir.name.removeprefix("run_")
        human_run_id = f"R{run_index:02d}"
        run_mapping.append([original_run_id, human_run_id])

        history_path = find_artifact(run_dir, "inference_history.json")
        usage_path = find_artifact(run_dir, "api_usage.json")
        if history_path is None:
            print(f"[WARNING] No inference_history.json in {run_dir}; skipping run.")
            continue
        history = load_json(history_path)
        if history is None:
            print(f"[WARNING] Invalid inference history in {run_dir}; skipping run.")
            continue
        usage_data = load_json(usage_path) if usage_path else {}
        usage_data = usage_data or {}
        params = history.get("agent_params") or (history.get("final_result") or {}).get("agent_params") or {}

        papers = extract_paper_paths(history)
        ds_hash = dataset_fingerprint(papers)
        if ds_hash not in dataset_ids:
            dataset_id = f"D{len(dataset_ids) + 1:02d}"
            dataset_ids[ds_hash] = dataset_id
            dataset_mapping.append([dataset_id, len(papers), "\n".join(papers)])
        dataset_id = dataset_ids[ds_hash]

        snapshot_path = find_artifact(run_dir, "prompt_snapshot.py")
        if snapshot_path:
            try:
                snapshot_bytes = snapshot_path.read_bytes()
                architecture_hash = hashlib.sha256(snapshot_bytes).hexdigest()
            except OSError as exc:
                print(f"[WARNING] Could not read prompt snapshot in {run_dir}: {exc}")
                architecture_hash = f"missing:{run_dir}"
        else:
            architecture_hash = f"missing:{run_dir}"
            print(f"[WARNING] No prompt_snapshot.py in {run_dir}")

        if architecture_hash not in architecture_ids:
            mode_for_id = extract_mode(params, run_dir)
            prefix = "M" if mode_for_id == "multi" else "S" if mode_for_id == "single" else "A"
            same_prefix_count = sum(1 for value in architecture_ids.values() if value.startswith(prefix))
            architecture_id = f"{prefix}{same_prefix_count + 1:02d}"
            architecture_ids[architecture_hash] = architecture_id
            architecture_mapping.append([
                architecture_id, mode_for_id,
                str(snapshot_path) if snapshot_path else "MISSING",
            ])
        architecture_id = architecture_ids[architecture_hash]

        mode = extract_mode(params, run_dir)
        model = extract_model(params, usage_data, history)
        run_metrics = extract_metrics(history, usage_data)

        # Totals come from the inference history (the same items that get scored);
        # the gaps/hypothesis txt files written by main.py are used as a cross-check.
        gaps, hypotheses = extract_items(history)
        txt_counts = {
            "gaps": count_txt_items(find_artifact(run_dir, "identified_research_gaps.txt"), "G"),
            "hypotheses": count_txt_items(find_artifact(run_dir, "proposed_hypothesis.txt"), "H"),
        }
        for label, from_history in (("gaps", len(gaps)), ("hypotheses", len(hypotheses))):
            if txt_counts[label] is not None and txt_counts[label] != from_history:
                print(f"[WARNING] {human_run_id}: {from_history} {label} in inference history "
                      f"but {txt_counts[label]} in the txt file.")

        metadata_rows.append([
            human_run_id, dataset_id, mode, model,
            extract_llm_params(params, usage_data), architecture_id,
            extract_max_rounds(params, mode),
            run_metrics["api_calls"], run_metrics["failed_calls"],
            run_metrics["input_tokens"], run_metrics["output_tokens"],
            run_metrics["total_tokens"],
            run_metrics["runtime_seconds"], run_metrics["pause_between_calls_seconds"],
            len(gaps), len(hypotheses),
        ])

        run_records.append({
            "human_run_id": human_run_id,
            "items": gaps + hypotheses,
        })
        print(f"[OK] {human_run_id} <- {original_run_id}: {len(gaps)} gaps, {len(hypotheses)} hypotheses")

    write_csv(analysis_dir / "01_run_id_mapping.csv", run_mapping)
    write_csv(analysis_dir / "02_dataset_id_mapping.csv", dataset_mapping)
    write_csv(analysis_dir / "03_architecture_id_mapping.csv", architecture_mapping)
    write_csv(analysis_dir / "04_run_metadata.csv", metadata_rows)
    write_csv(analysis_dir / "05_evaluation_scores.csv", build_score_rows(run_records))

    print(f"\nCreated 5 CSV files in: {analysis_dir}")
    print("  run_id_mapping.csv")
    print("  dataset_id_mapping.csv")
    print("  architecture_id_mapping.csv")
    print("  run_metadata.csv")
    print("  evaluation_scores.csv")


if __name__ == "__main__":
    main()