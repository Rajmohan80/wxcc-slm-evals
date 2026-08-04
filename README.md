# wxcc-slm-evals

RAG pipeline evaluation using RAGAS — wxcc-slm project

A reproducible, auditable evaluation of the [wxcc-slm](https://github.com/rajmohan80/wxcc-slm)
retrieval-augmented generation pipeline using [RAGAS](https://docs.ragas.io/).

This repo answers one question with real numbers:

> *"How do you know your RAG pipeline works, and how did you improve it?"*

---

## What is being evaluated

The system under test is the WxCC SLM pipeline — a domain-specific AI
consulting assistant for Cisco Webex Contact Center, built on:

| Component | Implementation |
|---|---|
| Embeddings | BGE-M3 (`BAAI/bge-m3`), dim 1024 |
| Vector store | Qdrant Cloud — `wxcc_slm_corpus`, 2,633 chunks |
| Retrieval | Cosine similarity, configurable top_k |
| Generation | Groq — Llama-3.3-70B-versatile |
| Orchestration | LangGraph intent flow |

Corpus: 41 Cisco Tier-1 primary sources covering WxCC architecture,
data locality, licensing, capacity/sizing, and compliance (EU AI Act,
India DoT, UAE PDPL).

---

## Results

### Baseline (top_k=8)

| Metric | Score |
|---|---|
| Answer relevancy | 0.7242 |
| Context precision | 0.9381 |
| Context recall | 0.8750 |
| Faithfulness | — (re-score pending) |

**Adversarial / hallucination resistance: 7/7 PASS**

The pipeline correctly:
- Abstained on out-of-scope questions (Brazil pricing, Amazon Connect capacity, Salesforce Apex)
- Fired a hard STOP on China deployment (not an available Country of Operation)
- Corrected false premises: "WxCC runs on GCP" → AWS; "US DC is Oregon" → N. Virginia
- Declined to design EU workplace emotion dashboards (EU AI Act Art 5(1)(f) prohibition)
- Correctly stated WebRTC is unavailable in the Indian domestic deployment model

### Experiment (top_k=5) — *scores pending*

| Metric | Baseline (top_k=8) | Experiment (top_k=5) | Delta |
|---|---|---|---|
| Answer relevancy | 0.7242 | — | — |
| Context precision | 0.9381 | — | — |
| Context recall | 0.8750 | — | — |
| Faithfulness | — | — | — |

*Results will be updated once the top_k=5 scoring run completes.*

---

## What the metrics mean

**Faithfulness** — are all claims in the answer supported by the retrieved
chunks? Low faithfulness = hallucination. Critical for a compliance domain
where a confident wrong answer about data residency is worse than no answer.

**Answer relevancy** — does the answer actually address the question? High
relevancy = on-topic and complete. The pipeline produces structured
consulting-style answers which score slightly lower on pure relevancy due
to verbosity — a known and documented trade-off.

**Context precision** — of the chunks retrieved, how many were actually
relevant? High precision = clean retrieval with little noise.

**Context recall** — did retrieval surface all the information the correct
answer needs? Low recall = the pipeline couldn't answer fully because the
right chunks never made it into context.

> **Judge model:** Groq `llama-3.1-8b-instant`. Using the same model family
> as the generator introduces a known self-preference risk. Mitigation: manual
> spot-checks of scored items, and planned re-run with a different judge family.
> This limitation is stated openly rather than hidden.

---

## Repository structure

```
wxcc-slm-evals/
  README.md                   this file
  SETUP.md                    full reproduction instructions
  requirements.txt            pinned dependencies
  golden_set/
    wxcc_golden_v1.jsonl      34 questions with ground truths (machine-readable)
    wxcc_golden_v1.md         34 questions with ground truths (human-readable)
  harness/
    run_pipeline.py           runs golden questions through the live pipeline
    patch_run.py              re-runs only failed rows (rate-limit recovery)
    score_ragas.py            scores with RAGAS + adversarial pass-fail check
  results/
    baseline_scores.md        baseline RAGAS scores (top_k=8)
    topk5_scores.md           experiment scores (top_k=5)
    compare.md                before/after delta table
  docs/
    AbhavTech_RAGAS_Build_Record.docx   formal build and validation record
```

---

## Golden test set design

34 questions across two categories:

**27 answerable** (scored with RAGAS metrics):
- 11 factual: data residency, region mapping, platform, compliance dates
- 8 capacity/sizing: deployment models, agent limits, DoT constraints
- 8 design guidance: UAE flagship, EU compliance flow, multilingual VAV2

**7 adversarial / out-of-scope** (scored pass-fail on hallucination resistance):
- 3 out-of-scope: questions with no corpus answer (Brazil pricing, Amazon Connect, Salesforce Apex)
- 4 adversarial: false-premise traps (GCP claim, Oregon claim, WebRTC domestic claim, EU emotion dashboard request)

Every ground truth traces to a named Cisco Tier-1 source document, verified
in the project's change registers before being added to the test set.

---

## Reproducing this evaluation

See [SETUP.md](SETUP.md) for full step-by-step instructions including
environment setup, the RAGAS VertexAI shim, and Groq token budget guidance.

Quick start:
```bat
:: from D:\project-slm-webex\ with .venv-eval active
python D:\Github\wxcc-slm-evals\harness\run_pipeline.py --golden golden_set\wxcc_golden_v1.jsonl --out results\run_baseline.jsonl --top_k 8
python D:\Github\wxcc-slm-evals\harness\score_ragas.py  --run results\run_baseline.jsonl --label baseline
```

---

## Related

- [wxcc-slm](https://github.com/rajmohan80/wxcc-slm) — the pipeline being evaluated
- [RAGAS documentation](https://docs.ragas.io/)
- [AbhavTech Consulting](https://abhavtech.com)
