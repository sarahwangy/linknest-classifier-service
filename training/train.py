"""
Fine-tunes distilbert-base-uncased on Linknest's bookmark categories.

Usage:
    python export_data.py          # writes training-data.jsonl
    python train.py                # writes ../model/ (loaded by the FastAPI service)
"""

import json
from pathlib import Path

import numpy as np
from datasets import Dataset
from sklearn.metrics import accuracy_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from labels import CATEGORIES, ID2LABEL, LABEL2ID

DATA_PATH = Path(__file__).parent / "training-data.jsonl"
MODEL_OUT = Path(__file__).parent.parent / "model"
BASE_MODEL = "distilbert-base-uncased"


def load_rows() -> list[dict]:
    if not DATA_PATH.exists():
        raise SystemExit("training-data.jsonl not found — run export_data.py first.")
    rows = []
    with open(DATA_PATH) as f:
        for line in f:
            row = json.loads(line)
            if row["aiCategory"] not in LABEL2ID:
                continue  # skip anything outside the known category set
            rows.append(row)
    if len(rows) < 20:
        raise SystemExit(
            f"Only {len(rows)} labeled rows found — need more data before fine-tuning "
            "is meaningful (aim for at least a few hundred)."
        )
    return rows


def main() -> None:
    rows = load_rows()
    print(f"Loaded {len(rows)} labeled bookmarks across {len(CATEGORIES)} categories")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def to_text(row: dict) -> str:
        return f"{row['title']} {row['description']}".strip()

    dataset = Dataset.from_list(
        [{"text": to_text(r), "label": LABEL2ID[r["aiCategory"]]} for r in rows]
    )
    dataset = dataset.train_test_split(test_size=0.15, seed=42)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

    tokenized = dataset.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(CATEGORIES),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {"accuracy": accuracy_score(labels, preds)}

    args = TrainingArguments(
        output_dir=str(MODEL_OUT / "_checkpoints"),
        num_train_epochs=4,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=10,
        learning_rate=5e-5,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    print(f"Final validation accuracy: {metrics['eval_accuracy']:.3f}")

    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_OUT)
    tokenizer.save_pretrained(MODEL_OUT)
    print(f"Saved fine-tuned model to {MODEL_OUT}")


if __name__ == "__main__":
    main()
