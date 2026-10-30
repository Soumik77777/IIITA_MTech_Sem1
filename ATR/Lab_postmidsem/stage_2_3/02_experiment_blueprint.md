# Experiment Blueprint

## Soumik Bhattacharyya, MDE2026005

## **Topic:** Single-LLM Versus Multi-Agent Debate Systems for Scientific Hypothesis Generation

## Broad Plan

The system will use LLM-based agents to identify research gaps and generate possible directions for exploration from a research topic or subfield and a collection of papers. The study will compare the cost and effectiveness of a single-LLM architecture against a multi-agent debate system. Experiments will vary the model family (local and cloud-based, general-purpose and domain-targeted models), model parameters, architecture, and prompts.

## Detailed Plan

**Input**

- Research topic or subfield.
- List of papers (paper discovery and collection will be automated in a later stage).
- Model name and version.
- Model parameters and inference settings, where applicable.

**Output**

- Identified research gaps or potential directions for exploration.
- Cost, including token usage and computational requirements such as runtime and GPU.
- Paper context and intermediate LLM outputs/logs from the different stages.

**Modules**

- `main.py`: Main entry point to configure experiment parameters and invoke the selected agent architecture.
- `single_llm.py`: Implements the single-LLM workflow, with auxiliary functions for logging and analysis.
- `multi_llm.py`: Implements the multi-agent workflow, with auxiliary functions for logging and analysis.

**Preprocessing**

Papers will be downloaded and organized into folders named by publication year. The initial collection will use the available paper list; automated paper discovery and downloading are planned for a later iteration.

**File Structure**

```text
root/
├── database/
│   └── papers/
│       └── trimmed_k_means/
│           ├── 2026/
│           ├── 2025/
│           ├── 2024/
│           └── ...
├── scripts/
│   ├── main.py
│   ├── single_llm.py
│   └── multi_llm.py
└── output/
    ├── run_<timestamp>_research_gaps.txt
    ├── run_<timestamp>_prompt_snapshot.py
    ├── run_<timestamp>_api_usage.json
    └── run_<timestamp>_inference_history.json
```

**Evaluation Metrics**

- **Human assessment:** Domain-informed assessment of each proposed gap or direction, considering novelty, feasibility, significance, clarity, grounding in the supplied papers, and the quality of supporting rationale. The assessment criteria and scoring rubric should be fixed before comparing systems.
- **Research-direction follow-up:** Apply a defined knowledge cutoff and examine whether later papers pursue similar directions in subsequent publication years. This can provide retrospective evidence of relevance, but it is not a definitive measure of idea quality: a useful idea may never be pursued, and later work may independently reach a similar direction.
- **Leakage and temporal-validity checks:** A forced knowledge cutoff may not be respected reliably by a model, so the cutoff must be treated as a limitation rather than a guarantee. Where possible, use papers published after the cutoff as a held-out set and check whether the model's outputs reveal information unavailable at the cutoff.
- **Cost and efficiency:** Record input/output tokens, API cost where applicable, runtime, and local compute requirements. Compare systems under equivalent input conditions.

**Computational Budget**

- Gemini Flash models may be available under free usage limits, subject to the provider's current quotas and terms. The usable token allowance and rate limits must be verified before each experiment.
- More capable models may require a paid API key. The exact budget will be determined through experimentation and recorded per run.
- Local models may require more RAM and compute than the current personal laptop can provide. Access to institute compute resources or GPUs may reduce direct compute costs, subject to availability and usage policies.

**Expected Final Comparison Table**

| Model | Simplified architecture | Response quality | Cost |
|---|---|---|---|
| To be filled from experiments | Single-LLM / multi-agent debate | To be measured using the predefined evaluation protocol | To be measured from actual usage and runtime |
