import os
import time
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import httpx
import mlflow
from mlflow.entities import SpanType
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from bank_data import SYSTEM_PROMPT

logger = logging.getLogger("fed-aura")

app = FastAPI()

MAAS_GATEWAY = os.environ.get(
    "MAAS_GATEWAY", "https://maas.apps.ocp.cloud.rhai-tmm.dev"
)
MAAS_MODEL = os.environ.get("MAAS_MODEL", "gemma4")
MAAS_API_KEY = os.environ.get("MAAS_API_KEY", "")
INFERENCE_URL = f"{MAAS_GATEWAY}/prelude-maas/{MAAS_MODEL}/v1/chat/completions"
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))

MLFLOW_EXPERIMENT = os.environ.get("MLFLOW_EXPERIMENT_NAME", "Fed Aura Capital")

try:
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    logger.info("MLflow experiment: %s", MLFLOW_EXPERIMENT)
except Exception as e:
    logger.warning("MLflow setup failed (traces will be skipped): %s", e)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    history = body.get("history", [])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MAAS_MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    headers = {"Content-Type": "application/json"}
    if MAAS_API_KEY:
        headers["Authorization"] = f"Bearer {MAAS_API_KEY}"

    async def event_stream():
        start = time.monotonic()
        first_token_time = None
        full_response = ""
        prompt_tokens = 0
        completion_tokens = 0
        error_occurred = False

        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST", INFERENCE_URL, json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        error_occurred = True
                        yield f"data: {json.dumps({'error': True, 'content': f'Model returned {resp.status_code}: {error_body.decode()[:200]}'})}\n\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            usage = chunk.get("usage")
                            if usage:
                                prompt_tokens = usage.get("prompt_tokens", 0)
                                completion_tokens = usage.get("completion_tokens", 0)

                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.monotonic()
                                full_response += content
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            except httpx.ConnectError as e:
                error_occurred = True
                yield f"data: {json.dumps({'error': True, 'content': f'Cannot reach model endpoint: {e}'})}\n\n"
                return

        elapsed = time.monotonic() - start
        ttft = (first_token_time - start) if first_token_time else elapsed

        if not error_occurred:
            try:
                _log_trace(
                    user_message=user_message,
                    assistant_response=full_response,
                    history_len=len(history),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    ttft_ms=round(ttft * 1000),
                    total_ms=round(elapsed * 1000),
                )
            except Exception as e:
                logger.warning("MLflow trace failed: %s", e)

        yield f"data: {json.dumps({'done': True, 'ttft_ms': round(ttft * 1000), 'total_ms': round(elapsed * 1000)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@mlflow.trace(name="fed-aura-chat", span_type=SpanType.CHAIN)
def _log_trace(
    user_message: str,
    assistant_response: str,
    history_len: int,
    prompt_tokens: int,
    completion_tokens: int,
    ttft_ms: int,
    total_ms: int,
):
    with mlflow.start_span(name="llm-inference", span_type=SpanType.CHAT_MODEL) as llm_span:
        llm_span.set_inputs({
            "model": MAAS_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": "(system prompt with bank data)"},
                {"role": "user", "content": user_message},
            ],
        })
        llm_span.set_outputs({
            "response": assistant_response,
            "finish_reason": "stop",
        })
        llm_span.set_attributes({
            "gen_ai.system": "vllm",
            "gen_ai.request.model": MAAS_MODEL,
            "gen_ai.request.max_tokens": MAX_TOKENS,
            "gen_ai.usage.prompt_tokens": prompt_tokens,
            "gen_ai.usage.completion_tokens": completion_tokens,
            "gen_ai.response.model": MAAS_MODEL,
            "ttft_ms": ttft_ms,
            "total_ms": total_ms,
        })

    return {"assistant_response": assistant_response}


@app.get("/health")
async def health():
    return {"status": "ok", "model": MAAS_MODEL, "gateway": MAAS_GATEWAY}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    tracking_uri = mlflow.get_tracking_uri()
    print(f"\n  Fed Aura Capital AI Advisor")
    print(f"  App:    http://localhost:{port}")
    print(f"  MLflow: {tracking_uri}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
