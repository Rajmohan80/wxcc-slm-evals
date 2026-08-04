"""
run_pipeline.py  --  Step 2 of the wxcc-slm RAGAS evaluation.

Runs every golden question through the LIVE SLM pipeline and records, per item:
    question, answer, contexts (raw retrieved chunk text), ground_truth,
    plus bookkeeping (category, type, top_k, stop/clarification flags, sources).

Why contexts are captured via retrieve() and NOT from SLMResponse.sources:
    SLMResponse.sources carries only chunk METADATA (filename, doc_id, score).
    RAGAS needs the raw chunk TEXT. So we call query_engine.retrieve() directly
    with the same top_k the pipeline uses, and pull the text field off each
    RetrievedChunk. The text attribute name is auto-detected at runtime so this
    script does not break if the field is called .text / .content / .chunk_text.

Run (from D:\\project-slm-webex\\, with .venv-eval active):
    python evals\\harness\\run_pipeline.py ^
        --golden evals\\golden_set\\wxcc_golden_v1.jsonl ^
        --out    evals\\results\\run_baseline.jsonl ^
        --top_k  8

Validation gate: the script prints a summary and every ANSWERABLE item must
have non-empty contexts. Abstention/STOP items may legitimately have empty
contexts (a hard STOP returns before retrieval) -- that is expected and noted.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# --- Windows console safety (emoji/unicode in answers won't crash stdout) ---
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- import the live pipeline + retriever from the project root -------------
# This script lives in evals\harness\ ; the pipeline modules are at project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from slm_pipeline import run as pipeline_run
    from query_engine import retrieve
except Exception as e:
    print("FATAL: could not import pipeline modules from", PROJECT_ROOT)
    print("       ", repr(e))
    print("Make sure you run this from D:\\project-slm-webex\\ with .venv-eval active.")
    sys.exit(1)


def detect_text_field(chunk):
    """Find which attribute on a RetrievedChunk holds the chunk text."""
    for name in ("text", "content", "chunk_text", "page_content", "body", "chunk"):
        val = getattr(chunk, name, None)
        if isinstance(val, str) and val.strip():
            return name
    # fall back: first string-valued attribute that looks like prose
    for name in dir(chunk):
        if name.startswith("_"):
            continue
        val = getattr(chunk, name, None)
        if isinstance(val, str) and len(val) > 40:
            return name
    return None


def get_contexts(query, top_k):
    """Return list[str] of raw chunk texts for a query, mirroring pipeline retrieval."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return [], None
    field = detect_text_field(chunks[0])
    if field is None:
        return [], None
    texts = []
    for c in chunks:
        v = getattr(c, field, None)
        if isinstance(v, str) and v.strip():
            texts.append(v.strip())
    return texts, field


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="evals/golden_set/wxcc_golden_v1.jsonl")
    ap.add_argument("--out",    default="evals/results/run_baseline.jsonl")
    ap.add_argument("--top_k",  type=int, default=8)
    ap.add_argument("--limit",  type=int, default=0, help="run only first N items (smoke test)")
    args = ap.parse_args()

    golden = [json.loads(l) for l in open(args.golden, encoding="utf-8") if l.strip()]
    if args.limit:
        golden = golden[:args.limit]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    print(f"Running {len(golden)} golden items through the live pipeline (top_k={args.top_k})...")
    print("-" * 70)

    detected_field = None
    rows = []
    empty_answerable = []

    for i, item in enumerate(golden, 1):
        q = item["question"]
        t0 = time.time()

        # 1) contexts: direct retrieval (what RAGAS scores retrieval on)
        contexts, field = get_contexts(q, args.top_k)
        if field:
            detected_field = field

        # 2) answer: full pipeline (STOP / clarification / generated)
        try:
            resp = pipeline_run(q, top_k=args.top_k)
            answer = resp.answer
            stop = resp.stop_condition
            clar = resp.clarification_needed
            sources = resp.sources
        except Exception as e:
            answer = f"[PIPELINE ERROR] {e!r}"
            stop = clar = sources = None

        dt = int((time.time() - t0) * 1000)

        row = {
            "id": item["id"],
            "category": item["category"],
            "type": item["type"],
            "question": q,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": item["ground_truth"],
            "source_ref": item.get("source", ""),
            "expected_behavior": item.get("expected_behavior", ""),
            "stop_condition": stop,
            "clarification_needed": clar,
            "n_contexts": len(contexts),
            "latency_ms": dt,
        }
        rows.append(row)

        flag = ""
        if item["category"] == "answerable" and len(contexts) == 0 and not stop:
            empty_answerable.append(item["id"])
            flag = "  <-- WARN: answerable but 0 contexts"
        elif stop:
            flag = f"  (STOP: {stop}, contexts intentionally empty)"

        print(f"[{i:2}/{len(golden)}] {item['id']} {item['category']:12} "
              f"ctx={len(contexts):2} {dt:5}ms{flag}")

    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("-" * 70)
    print(f"Wrote {len(rows)} rows -> {args.out}")
    print(f"Detected chunk text field: {detected_field}")
    n_ans = sum(1 for r in rows if r["category"] == "answerable")
    n_ans_ctx = sum(1 for r in rows if r["category"] == "answerable" and r["n_contexts"] > 0)
    print(f"Answerable items with contexts: {n_ans_ctx}/{n_ans}")
    if empty_answerable:
        print("WARN: answerable items returned 0 contexts:", ", ".join(empty_answerable))
        print("      (investigate retrieval before scoring -- RAGAS needs contexts)")
    else:
        print("GATE PASSED: every answerable item has non-empty contexts.")


if __name__ == "__main__":
    main()
