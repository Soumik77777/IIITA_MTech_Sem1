# Prompt 02 --- Evidence-Based Research Gap Matrix

**Student:** Soumik Bhattacharyya\
**Roll No.:** MDE2026005\
**Topic:** Single-LLM Versus Multi-Agent Debate Systems for Scientific
Hypothesis Generation

## Scope and evidence policy

This matrix is derived from the attached literature review, *Single-LLM
Versus Multi-Agent Debate Systems for Scientific Hypothesis Generation*.
References below use the review's own numbered citation scheme and
section/page locations. A statement in the review is not automatically
treated as a verified finding of the original paper. Where the review
does not provide enough detail to confirm an original study's dataset,
numerical results, or limitations, that is explicitly flagged for later
verification.

**Labels** - **REVIEW REPORTS:** What the current review says about a
cited study or research area. - **INFERENCE:** A candidate
interpretation or research opportunity derived from the review. -
**UNKNOWN / VERIFY:** Information that cannot be established from the
review alone.

## 1. Central methods covered by the review

  ----------------------------------------------------------------------------
  Method family     Description in    Review locations  Verification notes
                    the review        / references      
  ----------------- ----------------- ----------------- ----------------------
  Single-LLM        One model         Sections 1.2 and  The review summarizes
  generation        generates         2.1; references   the methods but does
                    hypotheses using  \[22\], \[23\].   not provide enough
                    prompts,                            implementation detail
                    scientific                          here to reproduce the
                    context, or                         studies directly.
                    data-driven                         Verify original
                    formulations.                       prompts, models,
                                                        datasets, and
                                                        evaluation protocols.

  Single-LLM        A single model    Section 1.2;      These are adjacent
  self-critique and generates,        Section 2.3;      general-purpose
  iterative         inspects, and     references \[13\] methods; their results
  refinement        revises an output Self-Refine and   should not be assumed
                    using feedback or \[15\] Reflexion. to transfer directly
                    memory.                             to scientific
                                                        hypothesis generation.

  Literature        Scientific        Section 2.1;      Verify the retrieval
  retrieval and     literature is     reference \[20\]  corpus, novelty
  novelty           retrieved to      SciMON.           objective, benchmarks,
  optimization      inspire or                          and reported outcomes
                    improve candidate                   from the original
                    ideas.                              paper.

  Multi-agent       Multiple agents   Sections 1.3 and  The review says debate
  debate            generate          2.3; references   can help some
                    proposals,        \[6\] and \[17\]. reasoning/factuality
                    critique or rebut                   tasks but is not
                    one another, and                    universally superior
                    synthesize or                       and depends on
                    rank results.                       task/configuration.
                                                        Verify the exact tasks
                                                        and quantitative
                                                        findings.

  Structured        Candidate ideas   Section 2.4;      Confirm the benchmark
  research-idea     are assessed on   references \[9\]  definitions,
  evaluation        multiple          IdeaBench and     annotators, scoring
                    dimensions rather \[14\] biomedical scales, and
                    than fluency      evaluation by Qi  inter-rater
                    alone.            et al.            reliability from the
                                                        originals.

  Experimental or   LLM-generated     Sections 2.4 and  The review mentions
  end-to-end        ideas are         3.5; references   experimental
  scientific        connected to      \[1\], \[3\],     validation, but
  workflows         coding,           \[5\], \[8\],     details and
                    experiments, or   \[12\], \[21\] as generalizability must
                    laboratory        cited in the      be checked against the
                    validation.       review.           individual papers.
  ----------------------------------------------------------------------------

## 2. Datasets and measured findings visible in the review

The review does **not** provide a consistent, consolidated dataset
inventory or a complete table of numerical results for all cited
methods. It explicitly states that the literature uses different
domains, prompts, models, datasets, expert panels, and evaluation scales
(Section 5, pp. 10--11 in the supplied PDF). It also notes that
biomedical results cannot automatically be generalized to other
scientific fields.

The review reports the following qualitative findings:

-   Single-LLM systems offer simplicity, lower cost, and easier control,
    especially when supported by suitable literature or domain tools
    (Abstract and Conclusion).
-   Multi-agent systems may improve exploration, criticism, and
    comparison of ideas when agents have complementary roles and
    meaningful diversity (Abstract; Sections 1.3 and 2.3).
-   Debate is not universally better than self-consistency or
    ensembling; performance depends on the task and debate strategy
    (Section 2.3, citing \[17\]).
-   LLM-based hypothesis quality cannot be judged from fluency alone;
    novelty, evidence grounding, plausibility, feasibility, and
    experimental validity need separate assessment (Sections 1.1 and
    2.4).
-   Retrospective evaluation can reward rediscovery of ideas already
    implicit in the available corpus; prospective evaluation is more
    difficult but better reflects contribution to actual discovery
    (Section 4.1).
-   Comparisons may be confounded by unequal token budgets, retrieval
    access, or model capability (Section 5).

**Numerical findings:** No common quantitative result table can be
reliably reconstructed from the review alone. Do not invent accuracy,
effect sizes, benchmark scores, sample counts, or costs. These must be
extracted from the original publications if they are needed for the
selected experiment.

## 3. Five candidate computational research gaps

### Gap 1 --- Controlled comparison of single-LLM stages and multi-agent debate

**Source evidence in the review** - Section 4.1, pp. 9--10: proposes
four matched conditions: single LLM with one generation, single LLM with
multiple sampled candidates, multi-agent without debate, and multi-agent
with structured debate. - Section 5, pp. 10--11: says comparisons are
often confounded by unequal token budgets, retrieval access, or model
capability. - Section 6, pp. 11--12: explicitly lists controlled
architecture comparisons and causal analysis of debate as research gaps.

**Review-reported limitation:** Existing comparisons may fail to isolate
architecture from extra computation, sampling, or information access.

**Inference:** A small controlled experiment can test whether structured
interaction improves a defined output-quality rubric beyond sequential
single-LLM refinement or multiple candidate sampling.

**Candidate research question:** Under matched input evidence and a
controlled generation budget, does structured multi-agent critique
improve the quality of generated scientific hypotheses compared with
single-LLM generation and single-LLM self-critique?

**Possible experiment:** Choose one narrow scientific domain and a
small, fixed set of research prompts or source papers. Compare (A)
one-shot single-LLM generation, (B) single-LLM generation plus
self-critique/revision, and (C) a small role-based multi-agent critique
condition. Keep the prompt, evidence, final output format, and
approximate call/token budget as comparable as feasible. Score outputs
using a predefined rubric; record calls, tokens if available, latency,
failures, and human review time.

**Evidence needed:** Candidate hypotheses, full prompts,
model/runtime/version, source documents, scores, resource logs, and a
clear account of deviations from matched conditions.

**Original-source verification needed:** Verify the exact comparisons
and limitations attributed to reference \[17\] and any other studies
used to motivate the experiment. This is a proposed experiment, not a
claim that the review has already demonstrated the outcome.

**Feasibility:** High relative to the other gaps if the domain and
source set are kept small.

------------------------------------------------------------------------

### Gap 2 --- Separating the effect of debate from additional sampling and computation

**Source evidence in the review** - Section 4.1, pp. 9--10: says the
four-condition design would help determine whether gains come from agent
interaction or simply from generating more candidates. - Section 6,
pp. 11--12: identifies causal analysis of debate as a research gap. -
Section 5, pp. 10--11: warns that additional agents introduce
engineering costs and comparisons may have unequal token budgets.

**Review-reported limitation:** The review identifies confounding
between agent interaction, parallel sampling, role specialization,
critique, and additional computation.

**Inference:** A staged ablation can reveal whether the critique/debate
step adds value beyond simply generating several candidates.

**Candidate research question:** When the number of candidate hypotheses
and the approximate generation budget are controlled, does adding a
critique-and-revision stage improve rubric-based quality compared with
selecting among multiple independently generated candidates?

**Possible experiment:** Compare (A) multiple independent candidates
with selection, (B) one candidate followed by single-LLM critique and
revision, and (C) multiple candidates followed by structured critique.
If feasible, add a multi-agent debate condition later. Keep the evidence
set fixed and report resource use.

**Evidence needed:** Candidate-level outputs before and after critique,
scoring rubric, per-stage prompts, number of model calls, token/latency
logs, and results across multiple prompts.

**Original-source verification needed:** The current review motivates
this gap but does not itself provide a controlled causal estimate. Check
original papers before making stronger claims about prior work.

**Feasibility:** Moderate to high. This can be combined with Gap 1
rather than treated as a separate full project.

------------------------------------------------------------------------

### Gap 3 --- Measuring conceptual diversity rather than paraphrase diversity

**Source evidence in the review** - Section 4.1, p. 9--10: states that a
set of ten paraphrases should not count as ten independent
discoveries. - Section 6, pp. 11--12: explicitly calls for better
diversity metrics that distinguish different mechanisms from
paraphrases. - Section 5, pp. 10--11: reports heterogeneous evaluation
scales across studies.

**Review-reported limitation:** The review identifies the need for
conceptual diversity measures but does not provide one validated
universal metric.

**Inference:** A small evaluation can compare simple text-similarity
measures with human judgments of whether hypotheses propose genuinely
different mechanisms or experiments.

**Candidate research question:** Do embedding-based similarity or
clustering methods reliably distinguish paraphrased hypotheses from
hypotheses proposing different mechanisms in a small scientific task?

**Possible experiment:** Generate a set of hypotheses for a fixed set of
prompts. Create or identify pairs that are paraphrases versus pairs that
differ in mechanism or experimental prediction. Use a small, explicitly
documented human annotation rubric and compare the labels with one or
more text-similarity/clustering measures.

**Evidence needed:** Anonymized hypothesis pairs, annotation
instructions, annotator judgments, similarity scores, agreement analysis
where possible, and examples of metric failures.

**Original-source verification needed:** Verify how diversity is defined
and measured in the studies cited by the review, including reference
\[9\] and other relevant work. The review's statement is a motivation,
not proof that a particular metric fails.

**Feasibility:** Moderate. The experiment is computationally manageable,
but reliable labels require careful annotation.

------------------------------------------------------------------------

### Gap 4 --- Evidence grounding and citation support in generated hypotheses

**Source evidence in the review** - Section 2.2, pp. 5--6: explains that
retrieval does not guarantee correctness; a model may misinterpret a
paper or cite evidence that does not entail a claim. - Section 5,
pp. 10--11: lists hallucinated mechanisms and references, unsupported
claims, and incorrect interpretations as important failure modes. -
Section 6.1, pp. 11--12: proposes evidence-driven interaction, including
retrieval and identifying falsifiers.

**Review-reported limitation:** Evidence grounding can fail even when a
system retrieves literature; the review does not establish that one
architecture consistently solves this problem.

**Inference:** Explicitly requiring each hypothesis to link claims to
passages in a fixed paper set may improve auditability, but it may also
increase runtime and not necessarily improve scientific validity.

**Candidate research question:** Does requiring explicit evidence links
to a fixed collection of scientific papers reduce unsupported claims in
generated hypotheses compared with generation from the same papers
without claim-level evidence tracing?

**Possible experiment:** Use a small curated set of papers and the same
model. Compare ordinary context-based generation with a condition
requiring each claim to cite a supporting passage. Manually verify
whether each cited passage actually supports the associated claim.

**Evidence needed:** Fixed source corpus, retrieval/context settings,
hypotheses, claim-to-passage links, a verification checklist,
unsupported-claim counts, and resource use.

**Original-source verification needed:** Verify the retrieval and
evidence-grounding methods in reference \[20\] and relevant
scientific-agent studies. Do not assume citation presence equals
citation correctness.

**Feasibility:** Moderate to high with a curated corpus; lower if live
web-scale retrieval is added immediately.

------------------------------------------------------------------------

### Gap 5 --- Adaptive escalation: when is multi-agent review worth its cost?

**Source evidence in the review** - Section 6.1, pp. 11--12: proposes
adaptive debate, where most candidates receive a lightweight single-LLM
pass and only candidates with high potential, substantial disagreement,
weak evidence, or safety concerns receive more agents. - Section 7,
pp. 12--13: proposes a selective hybrid pipeline and adaptive compute. -
Section 5, pp. 10--11: describes the engineering and computational costs
of multi-agent debate.

**Review-reported limitation:** Debate can be costly, and fixed agent
counts or debate rounds may spend resources on cases that do not benefit
from them.

**Inference:** A simple rule for escalating uncertain or weakly grounded
candidates may preserve quality while reducing average cost, but the
rule itself needs evaluation.

**Candidate research question:** Can a simple uncertainty- or
disagreement-based escalation rule achieve similar rubric-based
hypothesis quality to mandatory multi-agent review while using fewer
model calls or tokens?

**Possible experiment:** First run a single-LLM baseline on a small set
of prompts. Use a predefined signal---such as disagreement between two
independent ratings or missing evidence links---to decide which outputs
receive additional critique. Compare this selective condition with
always-on critique and no critique. Define the escalation rule before
inspecting final results.

**Evidence needed:** Escalation criteria, per-case routing decisions,
output scores, call/token counts, latency, and examples of cases where
escalation helped or failed.

**Original-source verification needed:** The review presents adaptive
debate as a future direction; it does not establish that the proposed
rule works. Search for closely related adaptive-compute or
selective-agent studies before claiming novelty.

**Feasibility:** Moderate. It is a natural extension after a working
baseline and a basic critique pipeline exist, but it should not be the
first implementation milestone.

## 4. Ranking of the three strongest candidates

Ranking criteria: research significance, availability of resources, and
implementation feasibility. This is a planning judgment, not a claim of
publication-level novelty.

  ------------------------------------------------------------------------------------------------
  Rank        Candidate              Significance   Resource       Feasibility   Reason
                                                    availability                 
  ----------- ---------------------- -------------- -------------- ------------- -----------------
  1           Gap 1: Controlled      High           High, if the   High          Directly
              comparison                            task uses a                  addresses the
                                                    small fixed                  review's central
                                                    corpus and                   comparison and
                                                    local model                  can begin with a
                                                                                 small number of
                                                                                 conditions.

  2           Gap 2: Isolating       High           High to        High to       Closely related
              debate from                           moderate       moderate      to Gap 1; a
              sampling/computation                                               staged ablation
                                                                                 can make the
                                                                                 result more
                                                                                 informative
                                                                                 without requiring
                                                                                 a large system.

  3           Gap 4: Evidence        High           Moderate to    Moderate to   Gives measurable,
              grounding and claim                   high with a    high          inspectable
              support                               curated paper                failure cases and
                                                    collection                   can be
                                                                                 implemented
                                                                                 before
                                                                                 general-purpose
                                                                                 live retrieval.
  ------------------------------------------------------------------------------------------------

Gap 3 is also feasible but requires careful annotation to validate the
diversity metric. Gap 5 is promising but depends on having a functioning
baseline and critique process first.

## 5. Recommended initial direction

**Provisional recommendation:** Start with Gap 1 and design it so that
Gap 2 can be examined through a small ablation. Use one narrow
scientific task, a fixed source set, and a local model through a
replaceable LangChain interface. Begin with a single-LLM baseline; do
not implement the full debate system before the baseline runs and
produces inspectable outputs.

The domain and dataset remain unselected. Select them only after
checking that the task has accessible source material, a defensible
scoring procedure, and a manageable amount of manual verification.

## 6. Verification checklist before treating claims as established

-   [ ] Verify the exact methods, datasets, model versions, prompts, and
    numerical results of references \[6\], \[9\], \[13\], \[14\],
    \[15\], \[17\], \[20\], \[22\], and \[23\] if they are used to
    justify the chosen experiment.
-   [ ] Check whether the original studies report limitations themselves
    or whether the limitation is inferred by the review author.
-   [ ] Check whether controlled comparisons or adaptive-debate studies
    published after the review have already examined the proposed
    question.
-   [ ] Do not claim novelty until a separate, documented literature
    search is completed.
-   [ ] Do not report any experimental result until the code has
    actually run and the output has been inspected.
