"""Run inside the test container via ECS Exec, without printing its API key."""

import json
import os
import urllib.error
import urllib.request

base_url = "http://127.0.0.1:8000"
api_key = os.environ.get("SERVICE_API_KEY")
if not api_key:
    raise RuntimeError("SERVICE_API_KEY is not configured")


def request(label, path, expected, payload=None, key=None):
    headers = {}
    data = None
    if key is not None:
        headers["X-API-Key"] = key
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            status, body = response.status, json.load(response)
    except urllib.error.HTTPError as error:
        status = error.code
        body = json.loads(error.read().decode())
    print(json.dumps({"test": label, "status": status, "response": body}), flush=True)
    if status != expected:
        raise AssertionError(f"{label}: expected {expected}, got {status}")
    return body


health = request("health", "/health", 200)
assert health.get("model_loaded") is True
sample = {
    "title": "Deploy FastAPI on Google Cloud Run",
    "description": "Docker, IAM and serverless deployment tutorial.",
}
result = request("classify", "/classify", 200, sample, api_key)
assert isinstance(result.get("category"), str)
assert 0 <= result["confidence"] <= 1
request("wrong_key", "/classify", 401, sample, "intentionally-invalid-test-key")
request("missing_key", "/classify", 401, sample)
request("empty_title", "/classify", 422, {"title": ""}, api_key)
print("SMOKE_TESTS_PASSED", flush=True)
