# PoC Decision Memo — Self-Hosted Classifier vs. LLM API for Bookmark Categorization

**Status:** Complete (local run) · **Date:** 2026-08-21 · **Owner:** Sarah Wang
**Related artefacts:** [`README.md`](./README.md) · [`training/train.py`](./training/train.py) · [`eval/compare.py`](./eval/compare.py)

---

## 1. Use Case & Hypothesis

Linknest classifies every imported bookmark into one of 18 categories by calling Claude Haiku
(`lib/claude.ts`). This is a small, structured, high-frequency, repeated task — a natural
candidate for a cheaper, faster, self-hosted alternative.

**Hypothesis:** A fine-tuned, self-hosted small model (DistilBERT) can replace the LLM API call
for this specific task without an unacceptable loss of accuracy, at meaningfully lower cost and
latency.

## 2. Scope

**In scope:** single-label classification of `title + description` into Linknest's existing
18-category taxonomy, using real production-labeled data (no synthetic data).

**Out of scope:** multi-label classification, categories not already present in production data,
re-training the routing logic inside Linknest itself.

## 3. Success Criteria (defined before the run)

| Metric | Target | Rationale |
|---|---|---|
| Accuracy | Within ~5 pts of Claude Haiku baseline (79.5%) | Below this, cost/latency gains don't offset the accuracy regression for a user-facing feature |
| Latency | Meaningfully lower than Haiku's ~900ms | Justifies the self-hosting effort |
| Cost | Nets out versus server rental at Linknest's current call volume | Otherwise no reason to switch |

## 4. Exit Criteria (defined before the run)

- **Proceed:** accuracy within target band → integrate as the default classifier behind a
  feature flag, keep Haiku as fallback.
- **Pivot:** accuracy below target but the failure mode is diagnosable and fixable (e.g. data
  quality, not model capacity) → fix the specific defect, re-run the same eval, re-decide.
- **Stop:** accuracy below target and the failure mode is structural (task genuinely needs a
  larger model's world knowledge) → keep Haiku, revisit only if call volume changes the cost math.

## 5. Approach

1. Exported 971 real labeled bookmarks directly from Linknest's production Neon DB
   (`training/export_data.py`) — not a synthetic or cherry-picked dataset.
2. Fine-tuned `distilbert-base-uncased` (4 epochs, CPU, ~47s) on an 85/15 train/test split.
3. Built an independent evaluation script (`eval/compare.py`) that runs **both** systems —
   Claude Haiku and the fine-tuned service — against the same 146-row held-out set (excluded from
   training), and reports accuracy, latency, and cost side by side.

## 6. Results

| | Accuracy | Avg latency | Avg cost/call | Total cost (146 calls) |
|---|---|---|---|---|
| Claude Haiku (current production) | 79.5% | 900ms | $0.000175 | $0.0255 |
| Fine-tuned DistilBERT (this service) | 55.5% | 24ms | $0 (excl. server rental) | $0 |

Latency and cost targets were met decisively (~37x faster, no per-call cost). **Accuracy missed
the target band by a wide margin** (24 pts below baseline, not the ~5 pts budgeted for).

## 7. Root Cause Analysis

The accuracy gap is not evidence the approach is unworkable — it traces to a specific, fixable
data problem: severe class imbalance. Several of the 17 categories have fewer than 10 training
examples, so the model has no meaningful signal for those classes. This was not visible from the
overall accuracy number alone; a per-class breakdown makes the imbalance the clear driver.

## 8. Recommendation: **Pivot**

Do not deploy as a drop-in replacement. Do not discard the approach either — the latency/cost
case is strong enough to justify one more iteration. Concretely:

1. Re-run `export_data.py` against a larger or rebalanced sample (oversample thin categories, or
   collapse near-empty categories per Linknest's own taxonomy review).
2. Add per-class precision/recall to `eval/compare.py` (currently overall accuracy only) so the
   next run's decision isn't based on a single aggregate number.
3. Re-run the same held-out comparison. If accuracy lands in the target band → proceed behind a
   feature flag. If not → stop, and treat Haiku as the settled answer for this task at current
   volume.

## 9. What This PoC Deliberately Did Not Claim

The write-up documents the tradeoff, not a win. "37x faster and free" is true and worth stating;
it is not, on its own, sufficient grounds to ship. A PoC's job is to produce evidence a
non-technical stakeholder can act on — this memo is that evidence, including the parts that don't
flatter the outcome.
