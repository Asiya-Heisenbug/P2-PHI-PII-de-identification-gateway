"""
Step 4 of the roadmap: fine-tune a small (≤1B param) transformer for
PHI/PII token classification (BIO tagging) on the synthetic dataset.

Base model: distilbert-base-uncased (66M params) — easy to justify in
MODEL_CARD.md, trains fast on CPU or a free Colab GPU. Swap MODEL_NAME
for e.g. "dslim/bert-base-NER" if you want a stronger starting checkpoint.

Usage:
    python model/training/train.py --data_dir data --out_dir model/adapter
"""

import argparse
import json
from pathlib import Path

import numpy as np
from datasets import Dataset, ClassLabel, Sequence, Features, Value
from transformers import (
    AutoTokenizer, AutoModelForTokenClassification,
    TrainingArguments, Trainer, DataCollatorForTokenClassification,
)
import evaluate as hf_evaluate  # pip install evaluate (pulled in by transformers/datasets extras)

MODEL_NAME = "distilbert-base-uncased"


def load_split(path, label_list):
    records = json.load(open(path))
    label2id = {l: i for i, l in enumerate(label_list)}
    return Dataset.from_dict({
        "tokens": [r["tokens"] for r in records],
        "ner_tags": [[label2id[t] for t in r["tags"]] for r in records],
    })


def build_label_list(data_dir):
    labels = {"O"}
    for split in ["train", "validation", "test"]:
        for r in json.load(open(Path(data_dir) / f"{split}.json")):
            labels.update(r["tags"])
    # O first, then sorted for determinism
    return ["O"] + sorted(l for l in labels if l != "O")


def tokenize_and_align(examples, tokenizer):
    tokenized = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)
    all_labels = []
    for i, labels in enumerate(examples["ner_tags"]):
        word_ids = tokenized.word_ids(batch_index=i)
        prev_word = None
        label_ids = []
        for wid in word_ids:
            if wid is None:
                label_ids.append(-100)
            elif wid != prev_word:
                label_ids.append(labels[wid])
            else:
                label_ids.append(-100)  # only tag first subtoken of each word
            prev_word = wid
        all_labels.append(label_ids)
    tokenized["labels"] = all_labels
    return tokenized


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="data")
    ap.add_argument("--out_dir", default="model/adapter")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch_size", type=int, default=8)
    args = ap.parse_args()

    label_list = build_label_list(args.data_dir)
    id2label = {i: l for i, l in enumerate(label_list)}
    label2id = {l: i for i, l in enumerate(label_list)}

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(label_list), id2label=id2label, label2id=label2id
    )

    train_ds = load_split(Path(args.data_dir) / "train.json", label_list)
    val_ds = load_split(Path(args.data_dir) / "validation.json", label_list)

    train_tok = train_ds.map(lambda ex: tokenize_and_align(ex, tokenizer), batched=True)
    val_tok = val_ds.map(lambda ex: tokenize_and_align(ex, tokenizer), batched=True)

    collator = DataCollatorForTokenClassification(tokenizer)
    seqeval = hf_evaluate.load("seqeval")

    def compute_metrics(p):
        preds = np.argmax(p.predictions, axis=2)
        true_preds, true_labels = [], []
        for pred, lab in zip(preds, p.label_ids):
            tp, tl = [], []
            for pi, li in zip(pred, lab):
                if li != -100:
                    tp.append(id2label[pi])
                    tl.append(id2label[li])
            true_preds.append(tp)
            true_labels.append(tl)
        res = seqeval.compute(predictions=true_preds, references=true_labels)
        return {
            "precision": res["overall_precision"],
            "recall": res["overall_recall"],
            "f1": res["overall_f1"],
        }

    args_tr = TrainingArguments(
        output_dir=args.out_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=5e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="recall",  # recall is the headline metric
    )

    trainer = Trainer(
        model=model, args=args_tr,
        train_dataset=train_tok, eval_dataset=val_tok,
        data_collator=collator, compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model(args.out_dir)
    tokenizer.save_pretrained(args.out_dir)
    with open(Path(args.out_dir) / "label_list.json", "w") as f:
        json.dump(label_list, f)
    print("Saved fine-tuned model to", args.out_dir)


if __name__ == "__main__":
    main()
