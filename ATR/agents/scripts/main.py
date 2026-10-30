"""ATR single-LLM research hypothesis prototype."""

import inspect
import json
import time
from pathlib import Path
from dotenv import load_dotenv

RUN_TIMESTAMP = str(round(time.time()))
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from single_llm_agent import run_single_agent
from multi_debate import run_multi_debate

# -------------------- CONFIGURATION --------------------
MODE = "multi"  # "single", "multi"
TOPIC = "Status and direction of outlier trimming in K-means and similar algorithms"
ADDITIONAL_PROMPT = ""

MODEL_NAME = "gemini-3.5-flash-lite" # gemini-3-flash-preview
TEMPERATURE = 0.2  # Used only if the selected model supports it.
MODEL_PARAMETER_ALLOWLIST = {
    "gemini-3.5-flash-lite": set(),
    "gemini-3-flash-preview": {"temperature"},
}

KNOWLEDGE_CUTOFF_YEAR = 2026
PAPERS_ROOT = Path("ATR/agents/dataset/papers/trimmed_k_means")
OUTPUT_ROOT = Path("ATR/agents/output")

# USD per 1 million tokens. None disables monetary estimates.
PRICE_PER_MILLION_TOKENS = {
    "gemini-3.5-flash-lite": {"input": None, "output": None},
    "gemini-3-flash-preview": {"input": None, "output": None},
}
# -------------------------------------------------------


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def replace_paper_names(data, pdf_paths):
    replacements = {
        path.name: str(path.resolve()) for path in pdf_paths
    }
    for old_path, new_path in {
        str(path): str(path.resolve()) for path in pdf_paths
    }.items():
        replacements[old_path] = new_path

    if isinstance(data, dict):
        return {k: replace_paper_names(v, pdf_paths) for k, v in data.items()}
    if isinstance(data, list):
        return [replace_paper_names(v, pdf_paths) for v in data]
    if isinstance(data, str):
        for old, new in replacements.items():
            data = data.replace(old, new)
    return data

def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    if MODE not in ("single", "multi"):
        raise ValueError("MODE must be 'single' or 'multi'.")
    if not TOPIC.strip():
        raise ValueError("TOPIC cannot be empty.")
    if MODEL_NAME not in MODEL_PARAMETER_ALLOWLIST:
        raise ValueError(
            f"No parameter allowlist defined for {MODEL_NAME}. "
            "Add its supported constructor parameters to MODEL_PARAMETER_ALLOWLIST."
        )

    pdf_paths = []
    for folder in PAPERS_ROOT.iterdir() if PAPERS_ROOT.exists() else []:
        if folder.is_dir() and folder.name.isdigit() and int(folder.name) <= KNOWLEDGE_CUTOFF_YEAR:
            pdf_paths.extend(folder.glob("*.pdf"))
            pdf_paths.extend(folder.glob("*.PDF"))
    pdf_paths = sorted(set(pdf_paths))

    if not pdf_paths:
        raise FileNotFoundError(
            f"No PDF files found under '{PAPERS_ROOT}' in year folders <= {KNOWLEDGE_CUTOFF_YEAR}."
        )

    agent_function = run_single_agent if MODE == "single" else run_multi_debate
    snapshot_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_prompt_snapshot.py"
    snapshot_path.write_text(inspect.getsource(agent_function), encoding="utf-8")

    allowed_parameters = MODEL_PARAMETER_ALLOWLIST[MODEL_NAME]
    llm_kwargs = {"model": MODEL_NAME}
    if "temperature" in allowed_parameters:
        llm_kwargs["temperature"] = TEMPERATURE

    llm = ChatGoogleGenerativeAI(**llm_kwargs)

    result = agent_function(
        llm=llm,
        topic=TOPIC,
        additional_prompt=ADDITIONAL_PROMPT,
        pdf_paths=pdf_paths,
        model_name=MODEL_NAME,
        price_per_million_tokens=PRICE_PER_MILLION_TOKENS.get(MODEL_NAME, {}),
    )

    result = replace_paper_names(result, pdf_paths)

    final_lines = [f"Research gap: {item}" for item in result.get("research_gaps", [])]
    for hypothesis in result.get("hypotheses", []):
        if isinstance(hypothesis, dict):
            final_lines.append(f"Hypothesis: {hypothesis.get('hypothesis', hypothesis)}")
        else:
            final_lines.append(f"Hypothesis: {hypothesis}")

    gaps_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_identified_research_gaps.txt"
    gaps_path.write_text(
        "\n\n".join(f"- {gap}" for gap in result.get("research_gaps", [])) + "\n",
        encoding="utf-8",
    )

    hypotheses_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_proposed_hypothesis.txt"
    hypotheses_path.write_text(
        "\n\n".join(
            f"- {h.get('hypothesis', h) if isinstance(h, dict) else h}"
            for h in result.get("hypotheses", [])
        ) + "\n",
        encoding="utf-8",
    )

    usage_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_api_usage.json"
    save_json(usage_path, {
        "run_timestamp": RUN_TIMESTAMP,
        "model": MODEL_NAME,
        "temperature_requested": TEMPERATURE,
        "temperature_applied": "temperature" in allowed_parameters,
        "usage_summary": result.get("usage_summary", {}),
        "calls": result.get("api_usage", []),
    })

    history_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_inference_history.json"
    if MODE == "multi":
        readable_history_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_inference_history.txt"
        readable_history_path.write_text(
            result.get("inference_history_text", ""),
            encoding="utf-8",
        )
    save_json(history_path, {
        "run_timestamp": RUN_TIMESTAMP,
        "agent_params": result.get("agent_params", {}),
        "events": result.get("inference_history", []),
        "final_result": result,
        "artifacts": {
            "identified_research_gaps": str(gaps_path),
            "proposed_hypothesis": str(hypotheses_path),
            "prompt_snapshot": str(snapshot_path),
            "api_usage": str(usage_path),
            "inference_history": str(history_path),
            "readable_inference_history": (str(readable_history_path) if MODE == "multi" else None),
        },
    })

    print(f"\nSaved identified research gaps: {gaps_path}")
    print(f"Saved proposed hypotheses: {hypotheses_path}")
    print(f"Saved API usage: {usage_path}")
    print(f"Saved inference history: {history_path}")
    print(f"Saved prompt snapshot: {snapshot_path}")
    if MODE == "multi":
        print(f"Saved readable inference history: {readable_history_path}")


if __name__ == "__main__":
    main()
