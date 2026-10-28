# Prompt and Decision History --- Prompt 01 Planning

**Student:** Soumik Bhattacharyya\
**Roll No.:** MDE2026005\
**Topic:** Single-LLM Versus Multi-Agent Debate Systems for Scientific
Hypothesis Generation

This log records the planning conversation used to prepare the initial
scope summary and research decisions. It does not claim that
implementation or experiments have taken place.

## 1. Initial Prompt Provided

> I am a postgraduate student converting my completed literature review
> into an implementation-based research paper. My topic is Single-LLM
> Versus Multi-Agent Debate Systems for Scientific Hypothesis
> Generation. Act as a critical research mentor and technical pair
> programmer.
>
> Guide me in stages: evidence-based gap identification,
> literature-to-experiment mapping, feasibility, research questions,
> verified baseline, coding, experimental evaluation, manuscript and
> reproducibility.
>
> Mark statements as VERIFIED, INFERRED or UNKNOWN, and explicitly
> request source files or outputs when evidence is missing. Never invent
> papers, datasets, repository links, code execution, experiments or
> metrics.
>
> Help me create a portable research_decisions.md log containing
> decisions, reasons, source/evidence and next actions. Start by asking
> me to attach my existing review and summarize its scope without
> assuming unseen content.

## 2. Initial Guidance

The assistant summarized the post-midsem task as a transition from a
literature review to a real computational study. It identified possible
directions from the review, including controlled comparisons of
single-LLM and multi-agent systems, the contribution of debate beyond
multiple sampling or self-critique, conceptual diversity,
quality-versus-cost trade-offs, and premature consensus.

The assistant recommended beginning with a small controlled comparison,
while making clear that this was a candidate direction rather than a
finalized experiment. It also emphasized that the initial planning task
did not require implementation yet.

## 3. Student's Initial Implementation Idea

> I am thinking of using a local LLM and LangChain to make a
> single-agent versus multi-agent comparison code. What should the
> different agents in the multi-agent system do? Check the paper; there
> is a proposed workflow for a multi-agent system with each agent doing
> something specific.
>
> It makes sense to start with a small domain, and later develop the
> agents so they can find papers on any relevant topic and come up with
> research gaps or scientific hypotheses.
>
> This is not what we are going to do for the final project yet. Based
> on these answers, we will make the Markdown files.

The assistant suggested these possible roles, based on the review's
proposed workflow:

1.  **Hypothesis Generator:** Propose candidate hypotheses.
2.  **Literature/Evidence Agent:** Retrieve relevant papers and connect
    claims to evidence.
3.  **Scientific Critic:** Check plausibility, assumptions, unsupported
    claims, and alternative explanations.
4.  **Feasibility Agent:** Assess whether a hypothesis can be tested
    with available data, tools, and resources.
5.  **Ranker/Synthesizer:** Compare candidates and critiques, preserve
    meaningful disagreement, and rank hypotheses.

The assistant also recommended a fair single-LLM baseline that can
generate, inspect evidence, critique, revise, and rank its own
proposals. It cautioned that a multi-agent system should not be favored
merely because it performs more stages.

## 4. Questions Asked by the Assistant and Student's Answers

### Question 1: Which small domain should be used?

**Student's answer:** The domain can be anything. Choose one with an
easily available dataset; the topic should preferably be experimental
and computational.

**Current implication:** The domain is not selected. Selection should
depend on data availability, a clear evaluation protocol, and
computational feasibility.

### Question 2: Which local LLM/runtime should be used?

**Student's answer:** Ollama is suitable, but LangChain supports
switching between models in the same code, so model choice need not be
settled now.

**Current implication:** Ollama is a candidate runtime, not a finalized
dependency. The code should ideally keep the model configurable.

### Question 3: Should paper retrieval be included immediately?

**Student's answer:** This depends on the difficulty and the intended
scope. The student suspects that Prompt 01's scope is outside this
implementation decision.

**Current implication:** Do not decide retrieval architecture
prematurely. First identify a feasible research question and determine
whether a curated paper collection is sufficient.

### Question 4: Is rubric-based evaluation acceptable?

**Student's answer:** Yes.

**Current implication:** A structured rubric can be considered, but
criteria, scoring consistency, and subjectivity must be addressed.

### Question 5: Should the project begin simply and expand later?

**Student's answer:** Yes. Start simple, but do not build the debate
systems yet.

**Current implication:** The current stage is planning only. Begin
implementation after selecting a research question and baseline.

## 5. Additional Student Instructions

> Regarding the missing references, I am short on time at the moment and
> can verify them later.
>
> Do not create the Markdown files yet; rather, discuss the questions at
> the end briefly.

The assistant then discussed the five questions and recommended a small
initial prototype with a curated paper collection, a local model, a
single-LLM baseline, and a multi-agent system added incrementally. The
student subsequently requested that the Markdown files be prepared.

## 6. Current Status

-   Existing literature review: available and used as the basis for
    scope.
-   Broad topic: established.
-   Local model/runtime: Ollama is a candidate; specific model not
    selected.
-   Framework: LangChain is preferred for model flexibility.
-   Domain and dataset: not selected.
-   Research question: not finalized.
-   Baseline: not implemented or verified.
-   Multi-agent debate system: not implemented; intentionally deferred.
-   Evaluation rubric: acceptable in principle, but not yet designed.
-   Missing references in the draft: verification deferred by the
    student.
-   Experimental results: none at this planning stage.

## 7. Immediate Next Actions

1.  Identify a small domain with accessible data and a clear
    computational evaluation.
2.  Check hardware and model-runtime feasibility.
3.  Extract candidate research gaps from the review and verify their
    supporting passages.
4.  Select one testable research question.
5.  Define and run a minimal baseline before adding agents.
6.  Record actual commands, outputs, settings, and verification results
    as implementation proceeds.
