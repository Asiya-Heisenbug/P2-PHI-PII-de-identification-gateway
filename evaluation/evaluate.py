"""
Step 12 of the roadmap: evaluate regex baseline, Presidio baseline, and our
fine-tuned model against the same test set, span-level (not just token-level).

Metrics:
  precision, recall, f1  -> standard span-overlap scoring
  leak_rate = missed_entities / total_entities  (this is the headline risk metric)

Usage:
    python evaluation/evaluate.py --test data/test.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines import regex_baseline, presidio_baseline
from src import detector


def spans_overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def score(gold_spans, pred_spans):
    """Span-level match: a gold entity counts as caught if any predicted
    span overlaps it (label-agnostic, since baselines use different label
    vocabularies — report a separate labeled breakdown alongside this)."""
    matched_gold = set()
    matched_pred = set()
    for gi, g in enumerate(gold_spans):
        for pi, p in enumerate(pred_spans):
            if spans_overlap(g[:2], p[:2]):
                matched_gold.add(gi)
                matched_pred.add(pi)
    tp = len(matched_gold)
    fn = len(gold_spans) - tp
    fp = len(pred_spans) - len(matched_pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    leak_rate = fn / len(gold_spans) if gold_spans else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "leak_rate": leak_rate,
            "tp": tp, "fp": fp, "fn": fn}


def macro_avg(per_note_scores):
    keys = ["precision", "recall", "f1", "leak_rate"]
    return {k: sum(s[k] for s in per_note_scores) / len(per_note_scores) for k in keys}


def run_system(name, detect_fn, records):
    per_note = []
    for r in records:
        gold = [(e["start"], e["end"], e["label"]) for e in r["entities"]]
        pred = detect_fn(r["text"])
        per_note.append(score(gold, pred))
    agg = macro_avg(per_note)
    agg["system"] = name
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default="data/test.json")
    ap.add_argument("--out", default="evaluation/results.csv")
    args = ap.parse_args()

    records = json.load(open(args.test))

    results = [
        run_system("regex", regex_baseline.detect, records),
        run_system("presidio", presidio_baseline.detect, records),
        run_system(f"our_model ({detector.mode()})", detector.detect, records),
    ]

    # Also report adversarial-only slice, since that's what the assessment
    # cares about most for a credible eval
    adv_records = [r for r in records if r.get("adversarial")]
    if adv_records:
        results.append(run_system(
            f"our_model_adversarial_only ({detector.mode()})", detector.detect, adv_records
        ))

    header = "system,precision,recall,f1,leak_rate\n"
    lines = [header]
    for r in results:
        lines.append(f"{r['system']},{r['precision']:.3f},{r['recall']:.3f},"
                      f"{r['f1']:.3f},{r['leak_rate']:.3f}\n")
        print(r)

    Path(args.out).write_text("".join(lines))
    print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
