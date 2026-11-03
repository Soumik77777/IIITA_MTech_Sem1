"""ATR research-gap and hypothesis-generation pipeline."""

import inspect
import json
import time
from pathlib import Path
from dotenv import load_dotenv

RUN_TIMESTAMP = str(round(time.time()))
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from single_agent import run_single_agent
from multi_agent_debate import run_multi_debate


# -------------------- CONFIGURATION --------------------
MODE = "single"  # "single" or "multi"
TOPIC = "Status and direction of outlier trimming in K-means and similar algorithms"
ADDITIONAL_PROMPT = ""
MODEL_NAME = "gemini-3.5-flash-lite"  # or "gemini-3-flash-preview"
TEMPERATURE = 0.2
MODEL_PARAMETER_ALLOWLIST = {
    "gemini-3.5-flash-lite": set(),
    "gemini-3-flash-preview": {"temperature"},
}
KNOWLEDGE_CUTOFF_YEAR = 2026
PAPERS_ROOT = Path("ATR/agents/dataset/papers/trimmed_k_means")
OUTPUT_ROOT = Path("ATR/agents/output")
PRICE_PER_MILLION_TOKENS = {
    "gemini-3.5-flash-lite": {"input": None, "output": None},
    "gemini-3-flash-preview": {"input": None, "output": None},
}
# -------------------------------------------------------


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_paper_fields(data, pdf_paths):
    """Rename legacy paper keys and normalize paper_loc values without substring replacement."""
    path_by_name = {Path(p).name: str(Path(p).resolve()) for p in pdf_paths}
    path_by_name.update({str(Path(p)): str(Path(p).resolve()) for p in pdf_paths})
    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            new_key = "paper_loc" if key == "paper" else key
            if new_key == "paper_loc" and isinstance(value, str) and value:
                value = path_by_name.get(value, path_by_name.get(Path(value).name, value))
            normalized[new_key] = normalize_paper_fields(value, pdf_paths)
        return normalized
    if isinstance(data, list):
        return [normalize_paper_fields(item, pdf_paths) for item in data]
    return data


def main():
    if MODE not in ("single", "multi"):
        raise ValueError("MODE must be 'single' or 'multi'.")
    if not TOPIC.strip():
        raise ValueError("TOPIC cannot be empty.")
    if MODEL_NAME not in MODEL_PARAMETER_ALLOWLIST:
        raise ValueError(f"No parameter allowlist defined for {MODEL_NAME}.")

    pdf_paths = []
    for folder in PAPERS_ROOT.iterdir() if PAPERS_ROOT.exists() else []:
        if folder.is_dir() and folder.name.isdigit() and int(folder.name) <= KNOWLEDGE_CUTOFF_YEAR:
            pdf_paths.extend(folder.glob("*.pdf"))
            pdf_paths.extend(folder.glob("*.PDF"))
    pdf_paths = sorted({Path(p).resolve() for p in pdf_paths})
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found under {PAPERS_ROOT} through {KNOWLEDGE_CUTOFF_YEAR}.")

    run_output_dir = OUTPUT_ROOT / f"run_{RUN_TIMESTAMP}"
    run_output_dir.mkdir(parents=True, exist_ok=True)
    agent_function = run_single_agent if MODE == "single" else run_multi_debate
    snapshot_path = run_output_dir / f"run_{RUN_TIMESTAMP}_prompt_snapshot.py"
    snapshot_path.write_text(inspect.getsource(agent_function), encoding="utf-8")

    kwargs = {"model": MODEL_NAME}
    if "temperature" in MODEL_PARAMETER_ALLOWLIST[MODEL_NAME]:
        kwargs["temperature"] = TEMPERATURE
    llm = ChatGoogleGenerativeAI(**kwargs)
    result = agent_function(
        llm=llm, topic=TOPIC, additional_prompt=ADDITIONAL_PROMPT,
        pdf_paths=pdf_paths, model_name=MODEL_NAME,
        price_per_million_tokens=PRICE_PER_MILLION_TOKENS.get(MODEL_NAME, {}),
    )
    result = normalize_paper_fields(result, pdf_paths)

    gaps_path = run_output_dir / f"run_{RUN_TIMESTAMP}_identified_research_gaps.txt"
    gaps_path.write_text("\n\n".join(f"- {x}" for x in result.get("research_gaps", [])) + "\n", encoding="utf-8")
    hypotheses_path = run_output_dir / f"run_{RUN_TIMESTAMP}_proposed_hypothesis.txt"
    hypotheses_path.write_text("\n\n".join(
        f"- {x.get('hypothesis', x) if isinstance(x, dict) else x}"
        for x in result.get("hypotheses", [])
    ) + "\n", encoding="utf-8")

    usage_path = run_output_dir / f"run_{RUN_TIMESTAMP}_api_usage.json"
    save_json(usage_path, {
        "run_timestamp": RUN_TIMESTAMP, "model": MODEL_NAME,
        "temperature_requested": TEMPERATURE,
        "temperature_applied": "temperature" in MODEL_PARAMETER_ALLOWLIST[MODEL_NAME],
        "usage_summary": result.get("usage_summary", {}),
        "calls": result.get("api_usage", []),
    })
    history_path = run_output_dir / f"run_{RUN_TIMESTAMP}_inference_history.json"
    artifacts = {
        "identified_research_gaps": str(gaps_path),
        "proposed_hypothesis": str(hypotheses_path),
        "prompt_snapshot": str(snapshot_path),
        "api_usage": str(usage_path),
        "inference_history": str(history_path),
    }
    readable_history_path = run_output_dir / f"run_{RUN_TIMESTAMP}_inference_history.txt"
    readable_history_path.write_text(result.get("inference_history_text", ""), encoding="utf-8")
    artifacts["readable_inference_history"] = str(readable_history_path)
    save_json(history_path, {
        "run_timestamp": RUN_TIMESTAMP,
        "agent_params": result.get("agent_params", {}),
        "events": result.get("inference_history", []),
        "final_result": result,
        "artifacts": artifacts,
    })
    print(f"\nSaved run directory: {run_output_dir}")
    for name, path in artifacts.items():
        print(f"Saved {name}: {path}")


if __name__ == "__main__":
    main()
