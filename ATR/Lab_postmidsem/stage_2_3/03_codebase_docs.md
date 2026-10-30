# Codebase Documentation

## Soumik Bhattacharyya, MDE2026005

## **Topic:** Single-LLM Versus Multi-Agent Debate Systems for Scientific Hypothesis Generation

## Scripts Directory

The current prototype uses a single-agent implementation, with a multi-agent implementation planned/in progress. The documented filenames reflect the current project context; confirm them against the latest repository before submission.

```text
scripts/
├── main.py
├── single_llm_agent.py
└── multi_agent.py
```

### `main.py`

**Purpose:** Entry point for configuring and running the selected research-gap generation workflow.

**Main blocks**

- **Environment setup:** Load environment variables from `.env` using `python-dotenv`. API keys must remain outside version control.
- **Input discovery:** Locate the paper PDFs organized in year-based folders under the trimmed k-means paper collection.
- **Run configuration:** Set the selected agent, model and applicable inference parameters.
- **Agent dispatch:** Call `run_single_agent` for the single-agent prototype. The multi-agent workflow will be connected through the corresponding module when its implementation is ready.
- **Run provenance:** Save a snapshot of the single-agent function source to `output/run_single_agent_snapshot.py` before execution, so the implementation associated with a run can be inspected later.
- **Execution and reporting:** Print the generated research gaps and record available usage, runtime, errors and intermediate inference details in output logs.

The exact configuration options and logging fields should be kept consistent with the current source code and recorded for each experiment.

### `single_llm_agent.py`

**Purpose:** Implements the single-LLM baseline used to identify research gaps from the supplied papers.

**Main blocks**

- **PDF text extraction:** Use `PdfReader` from `pypdf` to extract text from each paper.
- **Input validation:** Warn about PDFs that yield no usable text, such as scanned or empty files, and skip them rather than passing empty content to the model.
- **Prompt construction and inference:** Prepare the paper context and research task, then invoke the configured Google Gemini model through LangChain.
- **Output handling:** Return the generated research-gap response to the caller.
- **Usage and execution logging:** Record available token usage, runtime, errors and estimated cost where supported by the model response.

### `multi_agent.py`

**Purpose:** Implements the multi-agent workflow for research-gap generation and debate. This module is planned/in progress; its final agent roles, debate stages, parameters and logging should be documented after the implementation is finalized and tested.

## Dependencies

The following external Python packages correspond to the imports used or identified for the current prototype:

```text
pypdf
python-dotenv
langchain-google-genai
```

Standard-library modules used in the prototype include `pathlib`, `json`, `time`, `datetime` and `inspect`; these do not need to be listed in `requirements.txt`.

The imports `ChatGoogleGenerativeAI` and `run_single_agent` refer to the LangChain Gemini integration and the project's own single-agent module, respectively. The API key is loaded from the environment; do not include the key itself in this document or repository.

Dependency versions should be pinned in `requirements.txt` after confirming the versions in the working environment. Until then, the package names above are an initial dependency list, not a claim that a particular set of versions has been tested.
