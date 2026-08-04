"""
patch_run.py  --  re-run ONLY the failed rows of a run file and merge them back.

A row is "failed" if its answer starts with "[PIPELINE ERROR]" (e.g. the
generation hit a Groq rate limit). Retrieval/contexts are unaffected by rate
limits, so only the generated answer needs redoing.

This preserves every good row (including the expensive answerable ones) and
re-spends tokens only on the failures -- so the whole baseline fits in one
Groq daily budget alongside scoring.

Run (from D:\\project-slm-webex\\, .venv-eval active, AFTER Groq resets):
    python evals\\harness\\patch_run.py ^
        --run    evals\\results\\run_baseline.jsonl ^
        --golden evals\\golden_set\\wxcc_golden_v1.jsonl ^
        --top_k  8

It rewrites run_baseline.jsonl in place (after backing it up to
run_baseline.jsonl.bak) with the failed rows regenerated.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from slm_pipeline import run as pipeline_run
    from query_engine import retrieve
except Exception as e:
    print("FATAL: could not import pipeline modules:", repr(e))
    sys.exit(1)

ERROR_PREFIX = "[PIPELINE ERROR]"


def detect_text_field(chunk):
    for name in ("text", "content", "chunk_text", "page_content", "body", "chunk"):
        val = getattr(chunk, name, None)
        if isinstance(val, str) and val.strip():
            return name
    return None


def get_contexts(query, top_k):
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return []
    field = detect_text_field(chunks[0])
    if not field:
        return []
    return [getattr(c, field).strip() for c in chunks
            if isinstance(getattr(c, field, None), str) and getattr(c, field).strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run",    default="evals/results/run_baseline.jsonl")
    ap.add_argument("--golden", default="evals/golden_set/wxcc_golden_v1.jsonl")
    ap.add_argument("--top_k",  type=int, default=8)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.run, encoding="utf-8") if l.strip()]
    golden = {g["id"]: g for g in
              (json.loads(l) for l in open(args.golden, encoding="utf-8") if l.strip())}

    failed = [r for r in rows if str(r.get("answer", "")).startswith(ERROR_PREFIX)]
    if not failed:
        print("No failed rows found. Nothing to patch.")
        return

    print(f"Found {len(failed)} failed rows: {', '.join(r['id'] for r in failed)}")
    print(f"Re-running only these through the live pipeline (top_k={args.top_k})...")
    print("-" * 70)

    # back up before rewriting
    shutil.copy(args.run, args.run + ".bak")

    patched = {}
    for i, r in enumerate(failed, 1):
        item = golden.get(r["id"], {})
        q = r["question"]
        t0 = time.time()
        contexts = get_contexts(q, args.top_k)
        try:
            resp = pipeline_run(q, top_k=args.top_k)
            answer, stop, clar, sources = (resp.answer, resp.stop_condition,
                                           resp.clarification_needed, resp.sources)
        except Exception as e:
            answer = f"{ERROR_PREFIX} {e!r}"
            stop = clar = sources = None
        dt = int((time.time() - t0) * 1000)

        new = dict(r)
        new.update({
            "answer": answer, "contexts": contexts,
            "stop_condition": stop, "clarification_needed": clar,
            "n_contexts": len(contexts), "latency_ms": dt,
        })
        patched[r["id"]] = new
        ok = "OK" if not answer.startswith(ERROR_PREFIX) else "STILL FAILED"
        print(f"[{i}/{len(failed)}] {r['id']:4} {ok:12} ctx={len(contexts):2} {dt:6}ms")
        time.sleep(2)  # gentle pacing to avoid a fresh rate spike

    merged = [patched.get(r["id"], r) for r in rows]
    with open(args.run, "w", encoding="utf-8") as f:
        for r in merged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    still = [rid for rid, r in patched.items() if r["answer"].startswith(ERROR_PREFIX)]
    print("-" * 70)
    print(f"Merged {len(patched)} patched rows into {args.run} (backup: {args.run}.bak)")
    if still:
        print("STILL FAILED (token budget again?):", ", ".join(still))
    else:
        print("GATE PASSED: all previously-failed rows now have real answers.")


if __name__ == "__main__":
    main()
