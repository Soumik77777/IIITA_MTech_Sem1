# ATR — first working prototype

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set `GOOGLE_API_KEY` in your shell, or load it from a `.env` file using your
preferred environment-variable loader. The project does not load `.env`
automatically in this first version.

## 2. Add papers

Put selectable-text PDFs in year-named folders, for example:

```text
papers/
  2022/
    paper_a.pdf
  2024/
    paper_b.pdf
```

Only folders with numeric year names at or before `KNOWLEDGE_CUTOFF_YEAR`
are included. Scanned PDFs without a text layer are not OCR'd in this version.

## 3. Configure and run

Edit the configuration block at the top of `main.py`, then run:

```bash
python main.py
```

The first version processes each PDF separately, synthesizes research gaps
and candidate hypotheses, then asks the same model to critique and refine them.
It prints the result as JSON in the terminal.

## Usage and quota tracking

Every model call appends one JSON line to `output/api_usage.jsonl`, including
model, stage, runtime, input/output/total tokens when provided by the API, and
errors. Monetary cost is only estimated after you set current USD-per-million-
token rates in `main.py`; no price is guessed. This local log records this
program's requests, not account-wide Gemini quota consumption.

The similarity deduplication function is intentionally a no-op for now.
