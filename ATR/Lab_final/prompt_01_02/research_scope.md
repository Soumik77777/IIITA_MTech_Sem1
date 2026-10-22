# Research Scope Summary

**Student:** Soumik Bhattacharyya\
**Roll No.:** MDE2026005\
**Topic:** Single-LLM Versus Multi-Agent Debate Systems for Scientific
Hypothesis Generation

## Scope of the Existing Review

The literature review compares two broad approaches to scientific
hypothesis generation:

-   **Single-LLM systems:** One language model uses prompting,
    retrieval, self-reflection, or tools to generate and refine
    candidate hypotheses.
-   **Multi-agent systems:** Multiple model instances perform
    specialized roles and interact through critique, debate, iterative
    revision, or consensus.

The review considers hypothesis novelty, evidence grounding and
verification, critique and debate, evaluation of scientific quality, and
integration with broader research workflows. It argues that multi-agent
systems are not automatically superior: their potential benefits in
exploration, specialization, and criticism must be weighed against cost,
correlated errors, sycophancy, premature consensus, and other failure
modes.

The review proposes a conditional hybrid workflow: generate candidate
ideas, ground them in literature, evaluate them with specialized
critics, activate debate selectively when useful, and rank candidates
for possible experimental testing. It identifies controlled comparisons,
causal attribution of debate benefits, diversity measurement,
calibration, prospective validation, and human--AI collaboration as
areas needing further investigation.

## Current Implementation Direction

The initial implementation direction is to use a local LLM, with Ollama
as a possible runtime, and LangChain to keep model selection
replaceable. The exact model is not yet fixed.

The first prototype should remain small and experimentally manageable.
The domain should be selected based on the availability of an accessible
dataset or paper collection and the feasibility of computational
experiments. No domain or dataset has been selected yet.

The project is not yet committed to implementing the complete
multi-agent debate system. The immediate goal is to establish a feasible
research direction and begin with a simple baseline. Agent roles and
debate mechanisms will be developed incrementally only after the initial
setup and baseline are understood.

## Important Distinction

The review's proposed architecture is a research motivation, not an
experimentally validated implementation. No new experiments, metrics,
model performance, dataset availability, or novelty claims have been
established at this stage.

The existing draft contains some unresolved citation placeholders. These
will be verified later and should not be treated as confirmed evidence
until checked against the original publications.
