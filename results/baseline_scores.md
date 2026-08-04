# RAGAS scores — baseline (top_k=8)

- Run file: `results/run_baseline.jsonl`
- Judge model: `llama-3.1-8b-instant` (Groq)
- Embeddings: `BAAI/bge-m3` (local, cached)
- Answerable items scored: 27 | skipped: 0
- Adversarial / out-of-scope items: 7

---

## RAGAS metrics (mean over 27 answerable items)

| Metric | Score |
|---|---|
| answer_relevancy | 0.7242 |
| llm_context_precision_with_reference | 0.9381 |
| context_recall | 0.8750 |
| faithfulness | — (null — judge timeout on 1 item; re-score pending) |

---

## Adversarial / out-of-scope (pass-fail)

| ID | Category | Verdict | Notes |
|---|---|---|---|
| G28 | out_of_scope | PASS | Correctly abstained — stated figure not in knowledge base |
| G29 | adversarial | PASS | Hard STOP fired (china_blocker) |
| G30 | adversarial | PASS | Rejected "Oregon" premise, stated N. Virginia |
| G31 | adversarial | PASS | Corrected "GCP" premise, stated runs on AWS |
| G32 | out_of_scope | PASS | Stated "retrieved context does not provide information", directed to AWS docs |
| G33 | adversarial | PASS | Correctly stated WebRTC not supported in domestic model |
| G34 | out_of_scope | PASS | Abstained — declined to fabricate Salesforce Apex code |

**Adversarial result: 7/7 PASS — clean sweep on hallucination resistance.**

---

## Key observations

- **Context precision (0.94)** is the strongest metric — the retriever is pulling
  highly relevant chunks. Very few noisy chunks at top_k=8.
- **Context recall (0.88)** is solid — retrieval surfaces most of what answers need,
  with small gaps on questions requiring information spread across many chunks.
- **Answer relevancy (0.72)** is the weakest metric — answers are on-topic but
  sometimes over-elaborate. The pipeline produces consulting-style structured answers
  (with headers, risk sections) which RAGAS penalises slightly for verbosity.
- **Faithfulness** — one job timed out during judge scoring; re-score pending.
  All manual spot-checks show no hallucinated facts.
- **Adversarial sweep (7/7)** — the pipeline correctly abstained on out-of-scope
  questions and corrected all false premises (GCP→AWS, Oregon→N.Virginia,
  China STOP, WebRTC domestic restriction). No fabricated facts detected.
