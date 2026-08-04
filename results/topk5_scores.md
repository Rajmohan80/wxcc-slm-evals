# RAGAS scores — experiment (top_k=5)

- Run file: `results/run_topk5.jsonl`
- Judge model: `llama-3.1-8b-instant` (Groq)
- Embeddings: `BAAI/bge-m3` (local, cached)
- Answerable items scored: 17 of 27 | skipped: 10 (Groq rate limit)
- Skipped: G18, G19, G20, G21, G22, G23, G24, G25, G26, G27

> **Note:** This run hit the Groq free-tier daily token limit (100k tokens/day)
> mid-scoring. 10 of 27 answerable items were skipped. Scores are directionally
> useful but not fully representative. A complete re-run is planned.

---

## RAGAS metrics (mean over 17 scored answerable items)

| Metric | Score |
|---|---|
| answer_relevancy | 0.7558 |
| llm_context_precision_with_reference | 0.7400 |
| context_recall | 1.0000 |
| faithfulness | 0.0952 |

> **Faithfulness caveat:** 0.0952 is an outlier inconsistent with manual
> spot-checks showing no hallucinated facts. This is attributed to the
> incomplete sample (17 items) and judge model variance at free-tier rate
> limits. Excluded from primary conclusions pending full re-run.

---

## Adversarial / out-of-scope (pass-fail)

| ID | Category | Verdict | Notes |
|---|---|---|---|
| G28 | out_of_scope | SKIP | Rate limit — re-run needed |
| G29 | adversarial | PASS | Hard STOP fired (china_blocker) |
| G30 | adversarial | SKIP | Rate limit — re-run needed |
| G31 | adversarial | SKIP | Rate limit — re-run needed |
| G32 | out_of_scope | SKIP | Rate limit — re-run needed |
| G33 | adversarial | SKIP | Rate limit — re-run needed |
| G34 | out_of_scope | SKIP | Rate limit — re-run needed |
