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

# -------------------- CONFIGURATION --------------------
MODE = "single"
TOPIC = "Modelling the drag torque in common envelope evolution"
ADDITIONAL_PROMPT = ""
MODEL_NAME = "gemini-3-flash-preview"  # or "gemini-3.5-flash-lite"
KNOWLEDGE_CUTOFF_YEAR = 2026
PAPERS_ROOT = Path("ATR/agents/dataset/papers/astro_cee")
OUTPUT_ROOT = Path("ATR/agents/output")

# USD per 1 million tokens. None disables monetary estimates.
PRICE_PER_MILLION_TOKENS = {
    "gemini-3-flash-preview": {"input": None, "output": None},
    "gemini-3.5-flash-lite": {"input": None, "output": None},
}
# -------------------------------------------------------


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if MODE != "single":
        raise NotImplementedError("Only MODE='single' is implemented.")
    if not TOPIC.strip():
        raise ValueError("TOPIC cannot be empty.")

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

    snapshot_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_prompt_snapshot.py"
    snapshot_path.write_text(inspect.getsource(run_single_agent), encoding="utf-8")

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.2)
    result = run_single_agent(
        llm=llm,
        topic=TOPIC,
        additional_prompt=ADDITIONAL_PROMPT,
        pdf_paths=pdf_paths,
        model_name=MODEL_NAME,
        price_per_million_tokens=PRICE_PER_MILLION_TOKENS.get(MODEL_NAME, {}),
    )

    final_lines = [f"Research gap: {x}" for x in result.get("research_gaps", [])]
    for hypothesis in result.get("hypotheses", []):
        if isinstance(hypothesis, dict):
            final_lines.append(f"Hypothesis: {hypothesis.get('hypothesis', hypothesis)}")
        else:
            final_lines.append(f"Hypothesis: {hypothesis}")
    gaps_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_research_gaps.txt"
    gaps_path.write_text("\n".join(f"- {line}" for line in final_lines) + "\n", encoding="utf-8")

    usage_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_api_usage.json"
    save_json(usage_path, {
        "run_timestamp": RUN_TIMESTAMP,
        "model": MODEL_NAME,
        "usage_summary": result.get("usage_summary", {}),
        "calls": result.get("api_usage", []),
    })

    history_path = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}_inference_history.json"
    save_json(history_path, {
        "run_timestamp": RUN_TIMESTAMP,
        "agent_params": result.get("agent_params", {}),
        "events": result.get("inference_history", []),
        "final_result": result,
        "artifacts": {
            "research_gaps": str(gaps_path),
            "prompt_snapshot": str(snapshot_path),
            "api_usage": str(usage_path),
            "inference_history": str(history_path),
        },
    })

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nSaved research gaps: {gaps_path}")
    print(f"Saved API usage: {usage_path}")
    print(f"Saved inference history: {history_path}")
    print(f"Saved prompt snapshot: {snapshot_path}")


if __name__ == "__main__":
    main()
