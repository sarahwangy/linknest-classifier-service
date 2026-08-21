import os
from contextlib import asynccontextmanager
from pathlib import Path

import torch
from fastapi import FastAPI, Header, HTTPException
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.schemas import ClassifyRequest, ClassifyResponse

MODEL_PATH = Path(__file__).parent.parent / "model"
API_KEY = os.environ.get("SERVICE_API_KEY")

ml = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load once at process startup, reuse across every request — loading a few
    # hundred MB of weights per-request would make this pointlessly slow.
    ml["tokenizer"] = AutoTokenizer.from_pretrained(MODEL_PATH)
    ml["model"] = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    ml["model"].eval()
    yield
    ml.clear()


app = FastAPI(title="linknest-classifier-service", lifespan=lifespan)


def check_auth(x_api_key: str | None) -> None:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="SERVICE_API_KEY not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": "model" in ml}


@app.post("/classify", response_model=ClassifyResponse)
def classify(body: ClassifyRequest, x_api_key: str | None = Header(default=None)):
    check_auth(x_api_key)

    text = f"{body.title} {body.description}".strip()
    inputs = ml["tokenizer"](text, truncation=True, padding=True, max_length=128, return_tensors="pt")

    with torch.no_grad():
        logits = ml["model"](**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

    top_id = int(torch.argmax(probs).item())
    return ClassifyResponse(
        category=ml["model"].config.id2label[top_id],
        confidence=round(float(probs[top_id]), 4),
    )
