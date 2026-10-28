"""
ATR: first working single-LLM research hypothesis prototype.

Expected paper layout:
papers/
  2022/
    paper_a.pdf
  2023/
    paper_b.pdf

Install dependencies and set GOOGLE_API_KEY before running.
"""

from pathlib import Path
import inspect
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from single_llm_agent import run_single_agent

# -------------------- CONFIGURATION --------------------
MODE = "single"
TOPIC = "Enter the scientific research topic here"
ADDITIONAL_PROMPT = ""
MODEL_NAME = "gemini-3-flash-preview"  # or "gemini-3.5-flash-lite"
KNOWLEDGE_CUTOFF_YEAR = 2024

PAPERS_ROOT = Path("papers")
USAGE_LOG_PATH = Path("output/api_usage.jsonl")

# Fill these in from the current official pricing page if you want monetary
# estimates. Keep as None rather than silently reporting an inaccurate cost.
# Values are USD per 1 million tokens.
PRICE_PER_MILLION_TOKENS = {
    "gemini-3-flash-preview": {"input": None, "output": None},
    "gemini-3.5-flash-lite": {"input": None, "output": None},
}
# -------------------------------------------------------


def main():
    if MODE != "single":
        raise NotImplementedError(
            "Only MODE='single' is implemented. multi_agent.py is postponed."
        )

    if TOPIC.strip() == "" or TOPIC == "Enter the scientific research topic here":
        raise ValueError("Set TOPIC at the top of main.py before running.")

    # Select PDFs from year-named folders up to and including the cutoff year.
    pdf_paths = []
    for year_folder in PAPERS_ROOT.iterdir() if PAPERS_ROOT.exists() else []:
        if year_folder.is_dir() and year_folder.name.isdigit():
            if int(year_folder.name) <= KNOWLEDGE_CUTOFF_YEAR:
                pdf_paths.extend(year_folder.glob("*.pdf"))
                pdf_paths.extend(year_folder.glob("*.PDF"))

    pdf_paths = sorted(set(pdf_paths))
    if not pdf_paths:
        raise FileNotFoundError(
            f"No PDF files found under '{PAPERS_ROOT}' in year folders "
            f"<= {KNOWLEDGE_CUTOFF_YEAR}. Example: papers/2023/paper.pdf"
        )

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.2)

    result = run_single_agent(
        llm=llm,
        topic=TOPIC,
        additional_prompt=ADDITIONAL_PROMPT,
        pdf_paths=pdf_paths,
        model_name=MODEL_NAME,
        usage_log_path=USAGE_LOG_PATH,
        price_per_million_tokens=PRICE_PER_MILLION_TOKENS.get(MODEL_NAME, {}),
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

    Path("output").mkdir(parents=True, exist_ok=True)
    Path("output/run_single_agent_snapshot.py").write_text(
        inspect.getsource(run_single_agent), encoding="utf-8"
    )

    # Later: save result as a separate structured output file if desired.
    # output_path = Path("output/latest_result.json")
    # output_path.parent.mkdir(parents=True, exist_ok=True)
    # output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
