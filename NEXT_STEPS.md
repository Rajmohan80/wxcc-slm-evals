# Next Steps

This document records what is planned but not yet done. Everything here
is honest work-in-progress, not a claim of completion.

---

## 1. Complete the top_k=5 experiment

The top_k=5 scoring run was affected by Groq free-tier rate limits —
10 of 27 answerable items were skipped. The directional finding holds
(top_k=8 outperforms top_k=5 on precision), but a full uninterrupted
re-run is needed to confirm the faithfulness score and complete the
adversarial check.

**Planned action:** Re-run scoring on a fresh daily token budget with
pacing between judge calls to avoid hitting the per-minute limit.

---

## 2. Faithfulness re-score

Faithfulness came back at 0.09 on the partial top_k=5 run — an outlier
inconsistent with manual spot-checks that found no hallucinated facts.
This is attributed to judge model variance on an incomplete sample.

**Planned action:** Re-run faithfulness scoring on a complete baseline
run using a full uninterrupted session. Consider running the judge on a
different model family to cross-validate and rule out self-preference bias.

---

## 3. Online evaluation — A/B testing

The current RAGAS evaluation is offline: fixed questions, fixed answers,
fixed judge. This is the equivalent of a controlled lab test.

The next level is online evaluation with live traffic — serving two
pipeline configurations (for example top_k=8 vs top_k=5) to real users,
measuring which produces better outcomes on real queries. This requires
a traffic-splitting layer, guardrail metrics (latency, error rate), and
a minimum sample size for statistical significance.

**Planned action:** When wxcc-slm moves to a hosted deployment, instrument
it for A/B evaluation. The RAGAS offline scores provide the baseline to
beat; the online test validates whether the improvement holds under real
query distribution.

---

## 4. Prompt versioning

Prompts are currently embedded in the pipeline code. Every prompt change
is a code change, making it hard to trace which prompt version produced
which score.

**Planned action:** Extract all prompts into a `prompts/` directory with
one file per prompt, a version header (purpose, model, version, date,
reason for change), and a commit convention that links prompt changes to
evaluation results. This makes every score traceable to the exact prompt
that produced it.

---

## 5. Expand the golden set

The current 34-question set covers the corpus well but has gaps:
- No questions on WxCC licensing tiers
- No questions on Webex Calling integration specifics
- No questions on migration from UCCX

**Planned action:** Add 10-15 questions covering these areas as the corpus
expands. Version the new set as `wxcc_golden_v2.jsonl` and re-run the
full evaluation to show trend over time.

---

## 6. Reduce Groq token dependency

The evaluation currently depends entirely on Groq free-tier tokens, which
creates a daily budget constraint that interrupted two scoring runs.

**Planned action:** Evaluate an alternative local judge (for example
Ollama with Llama-3.1-8B running locally) so scoring can run without
hitting a remote rate limit. Compare local vs Groq judge scores on a
sample to validate consistency before switching.
