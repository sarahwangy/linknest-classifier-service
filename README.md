# linknest-classifier-service

Fine-tuned DistilBERT bookmark classifier served via FastAPI — a cost/latency
comparison against [Linknest](../6-bookmark/linknest)'s Claude Haiku
classification pipeline.

Standalone Python service, independent repo on purpose: Linknest calls this
over HTTP like any external API, the same way it already calls Anthropic/OpenAI.
No shared code, no shared deploy pipeline.

## Why

Linknest classifies every imported bookmark by calling Claude Haiku
(`lib/claude.ts`). That's a small, structured, repeated task — a natural
candidate to replace with a self-hosted fine-tuned model to see whether
accuracy holds up while cost and latency drop.

## Structure

```
training/
  labels.py         # category list — must match linknest's lib/claude.ts CATEGORIES
  export_data.py     # pulls labeled bookmarks straight from Neon (no Linknest API involved)
  train.py            # fine-tunes distilbert-base-uncased, writes ../model/
app/
  main.py             # FastAPI service — loads the model once at startup, serves /classify
  schemas.py          # request/response pydantic models
eval/
  compare.py          # 方案A (Claude Haiku) vs 方案B (this service) on held-out bookmarks
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SERVICE_API_KEY, ANTHROPIC_API_KEY
```

## 1. Export training data

```bash
cd training
export DATABASE_URL=...   # from linknest/.env.local
python export_data.py     # writes training-data.jsonl
```

## 2. Fine-tune

```bash
python train.py           # writes ../model/, prints validation accuracy
```

No HuggingFace account or API key needed — `distilbert-base-uncased` downloads
anonymously from the Hub. Runs on CPU (a few minutes for a few hundred rows).

## 3. Run the service locally

```bash
cd ..
export SERVICE_API_KEY=some-secret
uvicorn app.main:app --reload
curl -X POST localhost:8000/classify \
  -H "X-API-Key: some-secret" \
  -H "Content-Type: application/json" \
  -d '{"title": "Understanding Docker", "description": "A guide to containers"}'
```

## 4. Compare against Claude Haiku

```bash
cd eval
export ANTHROPIC_API_KEY=...
export SERVICE_URL=http://localhost:8000
export SERVICE_API_KEY=some-secret
python compare.py holdout.jsonl   # a slice of labeled bookmarks NOT used in training
```

Reports accuracy / avg latency / avg cost for both.

## Deploying

Build with the included `Dockerfile`, deploy to Render/Fly.io (persistent
container, not a serverless function — see the write-up on why Vercel isn't
the right fit for a model that needs to stay loaded in memory).

**Before deploying**: the `model/` directory is gitignored (it's a few hundred
MB of binary weights, doesn't belong in git history). Either commit it with
Git LFS, or add a step to the Docker build / container startup that downloads
it from wherever you're storing it (S3, HF Hub, etc.) — not yet solved here,
since no model has been trained against real data yet.

## Status (2026-08-21)

Run end-to-end locally (not yet deployed to Render):

- Exported 971 labeled bookmarks from Linknest's Neon DB
- Fine-tuned distilbert-base-uncased (4 epochs, CPU, ~47s) — **55.5% validation accuracy**
- Ran `eval/compare.py` against a 146-row held-out set (same train/test split, never trained on):

| | Accuracy | Avg latency | Avg cost/call | Total cost (146 calls) |
|---|---|---|---|---|
| Claude Haiku (current production) | 79.5% | 900ms | $0.000175 | $0.0255 |
| Fine-tuned DistilBERT (this service) | 55.5% | 24ms | $0 (self-hosted, excl. server rental) | $0 |

**Takeaway**: ~37x faster and free per-call, at a real accuracy cost — driven by
severe class imbalance in the training data (several of the 17 categories have
under 10 examples). Not a drop-in replacement for Linknest's production
classification as-is; the honest story is the tradeoff, not "it's better."

Still needed: deploy to Render/Fly.io, decide how the `model/` directory gets
into the deployed image (gitignored, not yet solved).
