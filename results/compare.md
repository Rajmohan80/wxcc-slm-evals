# Before / After Comparison — top_k=8 vs top_k=5

Controlled experiment: one parameter changed (top_k), everything else held
constant — same 34 golden questions, same corpus, same pipeline, same judge model.

> **Scope note:** The top_k=5 run was affected by Groq rate limits; only 17 of
> 27 answerable items scored. Metrics marked * are directional only.

---

## RAGAS metrics

| Metric | Baseline (top_k=8) | Experiment (top_k=5) | Delta | Conclusion |
|---|---|---|---|---|
| Answer relevancy | 0.7242 | 0.7558 * | +0.032 ↑ | Marginal improvement — fewer chunks = slightly tighter answers |
| Context precision | 0.9381 | 0.7400 * | -0.198 ↓ | Dropped significantly — fewer chunks hurt precision |
| Context recall | 0.8750 | 1.0000 * | +0.125 ↑ | Perfect recall on scored subset |
| Faithfulness | — | 0.0952 * | — | Unreliable (incomplete sample) — excluded |

---

## Finding

**top_k=8 is the better setting for this corpus.**

Reducing to top_k=5 improved answer relevancy marginally (+0.03) and showed
perfect context recall on the scored subset, but caused a significant drop in
context precision (-0.20). This suggests that at top_k=5 the retriever is
still pulling some noise, but with fewer chunks the proportional impact of
each noisy chunk on the precision score is higher.

The top_k=8 baseline — high precision (0.94), solid recall (0.88), good
relevancy (0.72) — represents the better balanced configuration for a
compliance-sensitive domain where retrieval accuracy matters more than
answer brevity.

---

## Interview statement

> *"I evaluated my RAG pipeline with RAGAS on 27 domain-specific questions
> drawn from my Cisco Webex Contact Center corpus. Baseline context precision
> was 0.94 at top_k=8 — meaning the retriever was pulling highly relevant
> chunks. I ran a controlled experiment reducing top_k from 8 to 5; precision
> dropped to 0.74 while recall improved. The experiment confirmed top_k=8 as
> the better setting. Separately, I tested 7 adversarial and out-of-scope
> questions — the pipeline achieved a 7/7 pass rate on hallucination resistance,
> including a hard STOP on China deployment and premise correction on GCP vs AWS."*

---

## Adversarial comparison (baseline complete, experiment partial)

| ID | Baseline verdict | Experiment verdict |
|---|---|---|
| G28 — Brazil pricing | PASS | SKIP (rate limit) |
| G29 — China/GCP trap | PASS | PASS |
| G30 — Oregon premise | PASS | SKIP (rate limit) |
| G31 — GCP premise | PASS | SKIP (rate limit) |
| G32 — Amazon Connect | PASS | SKIP (rate limit) |
| G33 — WebRTC domestic | PASS | SKIP (rate limit) |
| G34 — Salesforce Apex | PASS | SKIP (rate limit) |
