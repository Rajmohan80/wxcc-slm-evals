# Setup — wxcc-slm-evals

This repo evaluates the wxcc-slm RAG pipeline. It requires the parent
wxcc-slm project (`D:\project-slm-webex\`) to be present and working,
because the harness imports `slm_pipeline` and `query_engine` from it.

---

## Prerequisites

- Python 3.11
- wxcc-slm project at `D:\project-slm-webex\` with `.env` containing
  `GROQ_API_KEY` and `QDRANT_API_KEY`
- BGE-M3 model cached at `D:\hf_cache\` (do not re-download)

---

## Environment setup

From `D:\project-slm-webex\`:

```bat
py -3.11 -m venv .venv-eval
.venv-eval\Scripts\activate
pip install -r D:\Github\wxcc-slm-evals\requirements.txt
```

### Known issue — RAGAS VertexAI import

RAGAS 0.3.9 imports a removed langchain-community path. Apply this one-time shim:

```bat
python -c "import langchain_community.chat_models as m, os; p=os.path.join(os.path.dirname(m.__file__),'vertexai.py'); open(p,'w').write('class ChatVertexAI:\n    def __init__(self,*a,**k):\n        raise RuntimeError(\"VertexAI not used\")\n'); print('shim written')"
```

---

## Running the evaluation

All commands run from `D:\project-slm-webex\` with `.venv-eval` active.

### Step 1 — Run the pipeline against the golden set

```bat
python D:\Github\wxcc-slm-evals\harness\run_pipeline.py ^
    --golden D:\Github\wxcc-slm-evals\golden_set\wxcc_golden_v1.jsonl ^
    --out    D:\Github\wxcc-slm-evals\results\run_baseline.jsonl ^
    --top_k  8
```

### Step 2 — Score with RAGAS

```bat
python D:\Github\wxcc-slm-evals\harness\score_ragas.py ^
    --run   D:\Github\wxcc-slm-evals\results\run_baseline.jsonl ^
    --label baseline
```

### Step 3 — Run the experiment (top_k=5)

```bat
python D:\Github\wxcc-slm-evals\harness\run_pipeline.py ^
    --golden D:\Github\wxcc-slm-evals\golden_set\wxcc_golden_v1.jsonl ^
    --out    D:\Github\wxcc-slm-evals\results\run_topk5.jsonl ^
    --top_k  5

python D:\Github\wxcc-slm-evals\harness\score_ragas.py ^
    --run   D:\Github\wxcc-slm-evals\results\run_topk5.jsonl ^
    --label topk5
```

### If any rows fail (Groq rate limit)

```bat
python D:\Github\wxcc-slm-evals\harness\patch_run.py ^
    --run    D:\Github\wxcc-slm-evals\results\run_baseline.jsonl ^
    --golden D:\Github\wxcc-slm-evals\golden_set\wxcc_golden_v1.jsonl ^
    --top_k  8
```

---

## Token budget (Groq free tier — 100k tokens/day)

| Job | Approx tokens |
|---|---|
| Pipeline run (34 questions, top_k=8) | ~80,000 |
| RAGAS scoring (8B judge, 27 items) | ~15,000 |
| Total per experiment | ~95,000 |

Run the pipeline one day, score the next — or use two separate days for
baseline and experiment runs.
