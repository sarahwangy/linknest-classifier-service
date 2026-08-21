"""
方案A (Claude Haiku, via Anthropic API directly) vs 方案B (this repo's
fine-tuned FastAPI service) — run both against the same held-out bookmarks
and report accuracy / latency / cost.

Usage:
    export ANTHROPIC_API_KEY=...
    export SERVICE_URL=http://localhost:8000       # or the deployed Render URL
    export SERVICE_API_KEY=...
    python compare.py path/to/holdout.jsonl
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
import httpx

CATEGORIES = [
    "Technology", "Science", "Business", "Finance", "Health", "Entertainment",
    "Sports", "Politics", "Education", "Design", "Food", "Travel",
    "News", "Reference", "Shopping", "Social", "Productivity", "Uncategorized",
]

# Same pricing assumptions as linknest/lib/ai-logger.ts — USD per 1M tokens
HAIKU_PRICE = {"input": 1.0, "output": 5.0}

anthropic_client = anthropic.Anthropic()
SERVICE_URL = os.environ["SERVICE_URL"]
SERVICE_API_KEY = os.environ["SERVICE_API_KEY"]


def classify_with_claude(title: str, description: str) -> tuple[str, float, float]:
    prompt = f"""Classify this bookmark. Return ONLY valid JSON, no markdown.

Title: {title}
{f"Description: {description}" if description else ""}

Categories: {", ".join(CATEGORIES)}

Respond with exactly:
{{"category": "<one of the categories above>"}}"""

    start = time.time()
    msg = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=32,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.time() - start) * 1000

    cost = (
        msg.usage.input_tokens / 1_000_000 * HAIKU_PRICE["input"]
        + msg.usage.output_tokens / 1_000_000 * HAIKU_PRICE["output"]
    )
    try:
        category = json.loads(msg.content[0].text.strip())["category"]
    except Exception:
        category = "Uncategorized"
    return category, latency_ms, cost


def classify_with_finetuned(title: str, description: str) -> tuple[str, float, float]:
    start = time.time()
    resp = httpx.post(
        f"{SERVICE_URL}/classify",
        json={"title": title, "description": description},
        headers={"X-API-Key": SERVICE_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    latency_ms = (time.time() - start) * 1000
    category = resp.json()["category"]
    return category, latency_ms, 0.0  # self-hosted inference: no per-call token cost


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python compare.py path/to/holdout.jsonl")

    rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
    print(f"Comparing {len(rows)} held-out bookmarks (not used in training)\n")

    claude_correct = finetuned_correct = 0
    claude_latency_total = finetuned_latency_total = 0.0
    claude_cost_total = 0.0

    for i, row in enumerate(rows, 1):
        truth = row["aiCategory"]

        c_cat, c_ms, c_cost = classify_with_claude(row["title"], row.get("description", ""))
        f_cat, f_ms, f_cost = classify_with_finetuned(row["title"], row.get("description", ""))

        claude_correct += c_cat == truth
        finetuned_correct += f_cat == truth
        claude_latency_total += c_ms
        finetuned_latency_total += f_ms
        claude_cost_total += c_cost

        print(f"[{i}/{len(rows)}] truth={truth:14s} claude={c_cat:14s} finetuned={f_cat:14s}")

    n = len(rows)
    print("\n--- Results ---")
    print(f"Claude Haiku   accuracy={claude_correct/n:.1%}  avg_latency={claude_latency_total/n:.0f}ms  "
          f"avg_cost=${claude_cost_total/n:.6f}  total_cost=${claude_cost_total:.4f}")
    print(f"Fine-tuned     accuracy={finetuned_correct/n:.1%}  avg_latency={finetuned_latency_total/n:.0f}ms  "
          f"avg_cost=$0.000000 (self-hosted, excl. server rental)")


if __name__ == "__main__":
    main()
