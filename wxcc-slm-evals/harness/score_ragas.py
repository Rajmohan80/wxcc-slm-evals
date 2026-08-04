"""
score_ragas.py  --  Step 3 of the wxcc-slm RAGAS evaluation.

Reads a run file produced by run_pipeline.py and produces:
  1. RAGAS scores (faithfulness, answer_relevancy, context_precision,
     context_recall) over the ANSWERABLE items only.
  2. A pass/fail hallucination-resistance check over the ADVERSARIAL /
     OUT_OF_SCOPE items (these are not RAGAS-scorable -- there is no
     in-corpus ground truth to score against; correct behaviour is to
     abstain or correct a false premise).

Judge model : Groq llama-3.1-8b-instant  (cheap, fits the free tier)
Embeddings  : BGE-M3 local (answer_relevancy needs embeddings; kept offline
              and free by reusing the model already cached at D:\\hf_cache)

Rows whose answer begins with "[PIPELINE ERROR]" are SKIPPED and reported,
so a rate-limited or crashed generation never poisons the scores.

Run (from D:\\project-slm-webex\\, .venv-eval active):
    python evals\\harness\\score_ragas.py ^
        --run   evals\\results\\run_baseline.jsonl ^
        --label baseline
Outputs:
    evals\\results\\<label>_scores.json
    evals\\results\\<label>_scores.md
"""

import argparse
import json
import os
import sys
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# --- load .env so GROQ_API_KEY / QDRANT keys are available -------------------
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

JUDGE_MODEL = "llama-3.1-8b-instant"
ERROR_PREFIX = "[PIPELINE ERROR]"

# Phrases that indicate correct abstention / premise-correction. Used ONLY for
# the adversarial/out-of-scope pass-fail check, never for RAGAS scoring.
ABSTAIN_MARKERS = [
    "not available", "not in", "no data", "cannot find", "don't have",
    "do not have", "not covered", "out of scope", "outside the scope",
    "knowledge base", "not able to", "unable to", "no information",
    "not something i can", "i can't provide", "cannot provide",
]
CORRECTION_MARKERS = [  # for false-premise traps
    "not gcp", "runs on aws", "on aws", "actually aws",
    "not oregon", "n. virginia", "north virginia", "virginia",
    "not available", "hard blocker", "not supported", "prohibited",
    "article 5", "art 5", "5(1)(f)", "not webrtc", "webrtc is not",
    "no webrtc", "not in model", "only model 1", "international bpo",
]


def build_judge():
    from langchain_groq import ChatGroq
    from ragas.llms import LangchainLLMWrapper
    key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    if not key:
        print("FATAL: GROQ_API_KEY not found in environment/.env")
        sys.exit(1)
    llm = ChatGroq(model=JUDGE_MODEL, temperature=0.0, api_key=key)
    return LangchainLLMWrapper(llm)


def build_embeddings():
    """BGE-M3 local embeddings for answer_relevancy (offline, no token cost)."""
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    emb = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return LangchainEmbeddingsWrapper(emb)


def score_answerable(rows, judge, embeddings):
    from ragas import evaluate, EvaluationDataset
    from ragas.metrics import (
        Faithfulness, ResponseRelevancy,
        LLMContextPrecisionWithReference, LLMContextRecall,
    )

    data = []
    used, skipped = [], []
    for r in rows:
        if r["category"] != "answerable":
            continue
        if r["answer"].startswith(ERROR_PREFIX):
            skipped.append(r["id"])
            continue
        if not r["contexts"]:
            skipped.append(r["id"] + "(no-ctx)")
            continue
        data.append({
            "user_input": r["question"],
            "retrieved_contexts": r["contexts"],
            "response": r["answer"],
            "reference": r["ground_truth"],
        })
        used.append(r["id"])

    if not data:
        return None, used, skipped

    dataset = EvaluationDataset.from_list(data)
    metrics = [
        Faithfulness(llm=judge),
        ResponseRelevancy(llm=judge, embeddings=embeddings),
        LLMContextPrecisionWithReference(llm=judge),
        LLMContextRecall(llm=judge),
    ]
    result = evaluate(dataset=dataset, metrics=metrics, llm=judge, embeddings=embeddings)
    return result, used, skipped


def check_adversarial(rows):
    """Pass/fail: did the model abstain or correct the premise (not hallucinate)?"""
    out = []
    for r in rows:
        if r["category"] == "answerable":
            continue
        ans = r["answer"]
        low = ans.lower()
        if ans.startswith(ERROR_PREFIX):
            verdict, why = "SKIP", "pipeline error (rate limit / crash) — re-run needed"
        elif r.get("stop_condition"):
            verdict, why = "PASS", f"hard STOP fired ({r['stop_condition']})"
        else:
            hit = [m for m in (ABSTAIN_MARKERS + CORRECTION_MARKERS) if m in low]
            if hit:
                verdict, why = "PASS", "abstained / corrected premise: " + ", ".join(hit[:3])
            else:
                verdict, why = "REVIEW", "no abstention/correction marker — read manually"
        out.append({
            "id": r["id"], "category": r["category"], "verdict": verdict,
            "why": why, "question": r["question"], "answer_preview": ans[:300],
            "expected": r.get("expected_behavior", ""),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run",   default="evals/results/run_baseline.jsonl")
    ap.add_argument("--label", default="baseline")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.run, encoding="utf-8") if l.strip()]
    print(f"Loaded {len(rows)} rows from {args.run}")
    print(f"Judge model: {JUDGE_MODEL}")
    print("-" * 70)

    print("Scoring answerable items with RAGAS (this calls the judge LLM)...")
    judge = build_judge()
    embeddings = build_embeddings()
    result, used, skipped = score_answerable(rows, judge, embeddings)

    scores = {}
    if result is not None:
        try:
            df = result.to_pandas()
            for col in df.columns:
                if col in ("user_input", "retrieved_contexts", "response", "reference"):
                    continue
                vals = df[col].dropna()
                if len(vals):
                    scores[col] = round(float(vals.mean()), 4)
        except Exception:
            for k, v in dict(result).items():
                try:
                    scores[k] = round(float(v), 4)
                except Exception:
                    pass

    print("RAGAS scores (mean over answerable items):")
    for k, v in scores.items():
        print(f"   {k:35} {v}")
    print(f"Scored items: {len(used)}  |  skipped: {len(skipped)} {skipped or ''}")
    print("-" * 70)

    print("Adversarial / out-of-scope pass-fail check...")
    adv = check_adversarial(rows)
    for a in adv:
        print(f"   {a['id']} {a['category']:12} {a['verdict']:6} {a['why']}")

    # ---- write JSON ----------------------------------------------------------
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = Path(args.run).parent / f"{args.label}_scores.json"
    payload = {
        "label": args.label, "timestamp": ts, "run_file": str(args.run),
        "judge_model": JUDGE_MODEL, "ragas_scores": scores,
        "scored_ids": used, "skipped_ids": skipped,
        "adversarial_check": adv,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- write Markdown ------------------------------------------------------
    md = [f"# RAGAS scores — {args.label}", "",
          f"- Run file: `{args.run}`",
          f"- Judge model: `{JUDGE_MODEL}`",
          f"- Timestamp: {ts}",
          f"- Answerable items scored: {len(used)}  (skipped: {len(skipped)})",
          "", "## RAGAS metrics (mean over answerable items)", "",
          "| Metric | Score |", "|---|---|"]
    for k, v in scores.items():
        md.append(f"| {k} | {v} |")
    md += ["", "## Adversarial / out-of-scope (pass-fail)", "",
           "| ID | Category | Verdict | Notes |", "|---|---|---|---|"]
    for a in adv:
        md.append(f"| {a['id']} | {a['category']} | {a['verdict']} | {a['why']} |")
    if skipped:
        md += ["", f"> **Skipped:** {', '.join(skipped)} — rows with pipeline "
               f"errors (e.g. Groq rate limit) or missing contexts were excluded "
               f"so they do not distort the scores. Re-run those rows and re-score."]
    out_md = Path(args.run).parent / f"{args.label}_scores.md"
    out_md.write_text("\n".join(md), encoding="utf-8")

    print("-" * 70)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
