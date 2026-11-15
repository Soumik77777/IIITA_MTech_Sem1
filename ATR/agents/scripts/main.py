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
MODE = "multi"  # "single" or "multi"
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

# Run controls shared by both agents. They live here (not in the agent modules) so that changing them does not change the architecture snapshot of an agent.
MAX_ROUNDS = 3    # single: max self-critique + revision rounds; multi: max debate rounds per subject
PAUSE_SEC = 10     # minimum pause between consecutive API calls
MAX_RETRIES = 3   # attempts per API call (only retryable errors are retried)
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



import traceback
import importlib.metadata
from datetime import datetime, timezone


def _debug_json(value):
    """Convert diagnostic values to JSON-safe representations."""
    if hasattr(value, "model_json_schema"):
        try:
            return value.model_json_schema()
        except Exception:
            pass
    if hasattr(value, "schema") and callable(value.schema):
        try:
            return value.schema()
        except Exception:
            pass
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return repr(value)


class _LoggedRunnable:
    """Transparent invoke wrapper that records structured-output requests."""
    def __init__(self, runnable, log_path, request_id):
        self._runnable = runnable
        self._log_path = log_path
        self._request_id = request_id

    def __getattr__(self, name):
        return getattr(self._runnable, name)

    def invoke(self, input_data, *args, **kwargs):
        record = {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "event": "structured_invoke",
            "request_id": self._request_id,
            "input": repr(input_data),
            "invoke_kwargs": _debug_json(kwargs),
        }
        try:
            result = self._runnable.invoke(input_data, *args, **kwargs)
            record["status"] = "success"
            record["result_type"] = type(result).__name__
            # Record only metadata; full model outputs remain in inference history.
            if isinstance(result, dict):
                record["result_keys"] = list(result.keys())
                record["parsing_error"] = repr(result.get("parsing_error"))
            _append_debug(self._log_path, record)
            return result
        except Exception as exc:
            record.update({
                "status": "error",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
                "traceback": traceback.format_exc(),
            })
            _append_debug(self._log_path, record)
            raise


def _append_debug(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=repr) + "\\n")


class _LoggedLLM:
    def __init__(self, llm, log_path):
        self._llm = llm
        self._log_path = log_path
        self._counter = 0

    def __getattr__(self, name):
        return getattr(self._llm, name)

    def with_structured_output(self, *args, **kwargs):
        self._counter += 1
        request_id = self._counter

        schema = args[0] if args else kwargs.get("schema")

        _append_debug(self._log_path, {
            "event": "structured_output_setup",
            "request_id": request_id,
            "schema": _debug_json(schema),
            "method": kwargs.get("method"),
            "include_raw": kwargs.get("include_raw"),
        })

        runnable = self._llm.with_structured_output(*args, **kwargs)
        return _LoggedRunnable(runnable, self._log_path, request_id)


def install_structured_output_logger(llm, log_path):
    return _LoggedLLM(llm, log_path)


def _write_environment_diagnostics(path):
    packages = {}
    for package in (
        "langchain-core", "langchain-google-genai",
        "google-genai", "pydantic",
    ):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "not installed / distribution not found"
    _append_debug(path, {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event": "run_environment",
        "python": __import__("sys").version,
        "packages": packages,
    })

def main():
    if MODE not in ("single", "multi"):
        raise ValueError("MODE must be 'single' or 'multi'.")
    if not TOPIC.strip():
        raise ValueError("TOPIC cannot be empty.")
    if MODEL_NAME not in MODEL_PARAMETER_ALLOWLIST:
        raise ValueError(f"No parameter allowlist defined for {MODEL_NAME}.")
    if not isinstance(MAX_ROUNDS, int) or MAX_ROUNDS < 1:
        raise ValueError("MAX_ROUNDS must be an integer >= 1.")
    if PAUSE_SEC < 0:
        raise ValueError("PAUSE_SEC must be >= 0.")
    if not isinstance(MAX_RETRIES, int) or MAX_RETRIES < 1:
        raise ValueError("MAX_RETRIES must be an integer >= 1.")

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
    # Snapshot the WHOLE agent module (prompts, agent helpers, orchestration), not just
    # the entry function, so architecture can be analysed against performance later.
    snapshot_path = run_output_dir / f"run_{RUN_TIMESTAMP}_prompt_snapshot.py"
    snapshot_path.write_text(inspect.getsource(inspect.getmodule(agent_function)), encoding="utf-8")

    kwargs = {"model": MODEL_NAME}
    if "temperature" in MODEL_PARAMETER_ALLOWLIST[MODEL_NAME]:
        kwargs["temperature"] = TEMPERATURE
    debug_path = run_output_dir / f"run_{RUN_TIMESTAMP}_debug_{str(round(time.time()))}.jsonl"
    _write_environment_diagnostics(debug_path)
    llm = ChatGoogleGenerativeAI(**kwargs)
    llm = install_structured_output_logger(llm, debug_path)

    try:
        result = agent_function(
            llm=llm, topic=TOPIC, additional_prompt=ADDITIONAL_PROMPT,
            pdf_paths=pdf_paths, model_name=MODEL_NAME,
            price_per_million_tokens=PRICE_PER_MILLION_TOKENS.get(MODEL_NAME, {}),
            max_rounds=MAX_ROUNDS, pause_sec=PAUSE_SEC, max_retries=MAX_RETRIES,
        )
    except Exception as exc:
        _append_debug(debug_path, {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "event": "agent_pipeline_exception",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "traceback": traceback.format_exc(),
        })
        raise
    result = normalize_paper_fields(result, pdf_paths)

    research_gaps = result.get("research_gaps", [])
    hypotheses = result.get("hypotheses", [])
    if not research_gaps and not hypotheses:
        warnings = [result.get(key) for key in
                    ("parse_warning", "synthesis_warning", "critique_warning", "analysis_warning")]
        warning_text = "; ".join(str(x) for x in warnings if x)
        raise RuntimeError(
            "No research gaps or hypotheses were recovered; refusing to write empty output files. "
            + warning_text
        )

    gaps_path = run_output_dir / f"run_{RUN_TIMESTAMP}_identified_research_gaps.txt"
    gaps_path.write_text(
        "\n\n".join(f"- {item}" for item in research_gaps) + "\n",
        encoding="utf-8",
    )

    hypotheses_path = run_output_dir / f"run_{RUN_TIMESTAMP}_proposed_hypothesis.txt"
    hypothesis_blocks = []
    for item in hypotheses:
        if isinstance(item, dict):
            text = f"{item.get('id', '')}: {item.get('hypothesis', '')}".strip()
            if item.get("rationale"):
                text += f"\nRationale: {item['rationale']}"
            if item.get("testable_prediction"):
                text += f"\nTestable prediction: {item['testable_prediction']}"
            if item.get("caveats"):
                text += f"\nCaveats: {item['caveats']}"
            refs = item.get("supporting_papers", [])
            paper_ids = [ref.get("paper_id") for ref in refs if isinstance(ref, dict) and ref.get("paper_id")]
            if paper_ids:
                text += "\nReferences: " + ", ".join(paper_ids)
        else:
            text = str(item)
        hypothesis_blocks.append("- " + text)
    hypotheses_path.write_text("\n\n".join(hypothesis_blocks) + "\n", encoding="utf-8")

    usage_path = run_output_dir / f"run_{RUN_TIMESTAMP}_api_usage.json"
    save_json(usage_path, {
        "run_timestamp": RUN_TIMESTAMP, "model": MODEL_NAME,
        "temperature_requested": TEMPERATURE,
        "temperature_applied": "temperature" in MODEL_PARAMETER_ALLOWLIST[MODEL_NAME],
        "structured_output": {"enabled": True, "method": "json_schema"},
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
        "debug_log": str(debug_path),
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
    print(f"Saved debug log: {debug_path}")
    for name, path in artifacts.items():
        print(f"Saved {name}: {path}")


if __name__ == "__main__":
    main()