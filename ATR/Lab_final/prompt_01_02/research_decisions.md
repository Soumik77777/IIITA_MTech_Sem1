# Research Decisions Log

**Student:** Soumik Bhattacharyya\
**Roll No.:** MDE2026005\
**Research topic:** Single-LLM Versus Multi-Agent Debate Systems for
Scientific Hypothesis Generation

This is an initial planning log. Decisions are provisional unless marked
otherwise. No experiments or implementation results are claimed.

  ------------------------------------------------------------------------------
  ID             Decision or      Status         Reason /       Next action
                 question                        evidence       
  -------------- ---------------- -------------- -------------- ----------------
  D1             Use the existing VERIFIED       The review     Use the review
                 literature                      compares       to develop
                 review as the                   single-LLM and candidate
                 starting point.                 multi-agent    research
                                                 approaches to  questions.
                                                 scientific     
                                                 hypothesis     
                                                 generation and 
                                                 identifies     
                                                 research gaps. 

  D2             Explore a        INFERRED /     This follows   Narrow the
                 computational    provisional    the review     comparison to
                 comparison of a                 topic and its  one testable
                 single-LLM                      identified gap question and a
                 workflow and a                  around         feasible scope.
                 multi-agent                     controlled     
                 workflow.                       architecture   
                                                 comparisons.   

  D3             Use LangChain to PROPOSED       The student    Verify current
                 organize the                    prefers model  package support
                 code and allow                  flexibility    and choose a
                 different models                rather than    minimal
                 to be selected                  committing to  environment when
                 without                         one model at   implementation
                 redesigning the                 the planning   begins.
                 whole pipeline.                 stage.         

  D4             Consider Ollama  PROPOSED       The student    Check hardware,
                 for local model                 identified     model size,
                 execution.                      Ollama as a    context length,
                                                 suitable       and runtime
                                                 option but has feasibility
                                                 not selected a before choosing
                                                 specific       a model.
                                                 model.         

  D5             Start with a     PROPOSED       A narrow scope Compare
                 small scientific                should reduce  candidate
                 domain and an                   retrieval and  domains based on
                 accessible                      evaluation     accessible data,
                 dataset or                      complexity and clear
                 curated paper                   make errors    evaluation, and
                 collection.                     easier to      computational
                                                 inspect.       feasibility.

  D6             Begin with a     AGREED         The student    Define the
                 simple working                  explicitly     smallest useful
                 baseline before                 prefers an     baseline and
                 building debate                 incremental    verify it runs
                 mechanisms.                     approach and   before adding
                                                 does not want  components.
                                                 to build the   
                                                 debate systems 
                                                 yet.           

  D7             A future         INFERRED /     These roles    Add roles one at
                 multi-agent      provisional    are consistent a time only when
                 prototype may                   with the       their
                 separate                        workflow and   contribution can
                 hypothesis                      specialized    be evaluated.
                 generation,                     functions      
                 evidence                        discussed in   
                 retrieval,                      the review.    
                 scientific                                     
                 criticism,                                     
                 feasibility                                    
                 assessment, and                                
                 ranking.                                       

  D8             The single-LLM   PROPOSED       A fair         Define matched
                 baseline should                 comparison     inputs, outputs,
                 be allowed to                   should not     evaluation
                 use sequential                  artificially   criteria, and
                 generation,                     restrict the   resource
                 evidence review,                single-LLM     reporting.
                 self-critique,                  condition to   
                 and revision.                   one prompt     
                                                 while giving   
                                                 the            
                                                 multi-agent    
                                                 condition      
                                                 several        
                                                 stages.        

  D9             Initial          AGREED, with   The student is Define criteria,
                 evaluation can   limitations    comfortable    scoring
                 use a structured                with           instructions,
                 rubric.                         rubric-based   and limitations
                                                 evaluation;    before
                                                 some quality   evaluating
                                                 dimensions may outputs.
                                                 be subjective. 

  D10            Do not claim     AGREED /       Novelty        Initially assess
                 that the system  precaution     requires       evidence
                 generates novel                 comparison     grounding,
                 scientific                      with existing  plausibility,
                 discoveries at                  literature and feasibility,
                 this stage.                     may require    diversity, and
                                                 expert         cost; treat
                                                 assessment.    novelty as
                                                                unverified
                                                                unless tested.

  D11            Verify           DEFERRED       The student is Return to the
                 unresolved                      short on time  original papers
                 citations in the                and plans to   before using
                 current draft                   verify missing those claims as
                 later.                          references     confirmed
                                                 later.         evidence in the
                                                                final research
                                                                paper.

  D12            Do not create    AGREED         The current    Complete scope
                 implementation                  task is        and gap analysis
                 or debate-system                planning and   first.
                 code at this                    preparing the  
                 stage.                          Prompt 01      
                                                 outputs, not   
                                                 implementing   
                                                 the final      
                                                 project.       
  ------------------------------------------------------------------------------

## Open Questions

1.  Which scientific domain offers an accessible dataset or paper
    collection and a clear computational evaluation?
2.  What hardware is available for local inference, and what model sizes
    can it run reliably?
3.  Should the first experiment use a curated paper collection or
    include retrieval from an external paper source?
4.  Which evaluation criteria can be scored consistently, and which
    require human judgment?
5.  What is the smallest baseline that can run and produce inspectable
    outputs?

## Evidence Labels

-   **VERIFIED:** Directly supported by the current review or explicitly
    confirmed by the student.
-   **INFERRED:** A reasoned interpretation of the review or project
    constraints; not yet demonstrated.
-   **UNKNOWN:** Evidence is missing or the decision has not been made.

## Next Actions

1.  Select a small, experimentally manageable domain based on accessible
    data.
2.  Check hardware and local-model feasibility.
3.  Identify candidate research gaps in the review and verify their
    supporting passages.
4.  Choose one narrow research question.
5.  Define a baseline and an evaluation protocol before implementing
    additional agents.
6.  Verify all important source claims, data access, and model/runtime
    details before relying on them.
