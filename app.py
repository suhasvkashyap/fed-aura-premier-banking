import os
import time
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response

from bank_data import SYSTEM_PROMPT

app = FastAPI()

MAAS_GATEWAY = os.environ.get(
    "MAAS_GATEWAY", "https://maas.apps.ocp.cloud.rhai-tmm.dev"
)
MAAS_MODEL = os.environ.get("MAAS_MODEL", "gemma4")
MAAS_API_KEY = os.environ.get("MAAS_API_KEY", "")
INFERENCE_URL = f"{MAAS_GATEWAY}/prelude-maas/{MAAS_MODEL}/v1/chat/completions"
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.get("/logo.svg")
async def logo():
    svg_path = Path(__file__).parent / "fed-aura-logo.svg"
    return Response(svg_path.read_text(), media_type="image/svg+xml")


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
    }

    headers = {"Content-Type": "application/json"}
    if MAAS_API_KEY:
        headers["Authorization"] = f"Bearer {MAAS_API_KEY}"

    async def event_stream():
        start = time.monotonic()
        first_token_time = None

        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST", INFERENCE_URL, json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
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
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.monotonic()
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

            except httpx.ConnectError as e:
                yield f"data: {json.dumps({'error': True, 'content': f'Cannot reach model endpoint: {e}'})}\n\n"
                return

        elapsed = time.monotonic() - start
        ttft = (first_token_time - start) if first_token_time else elapsed
        yield f"data: {json.dumps({'done': True, 'ttft_ms': round(ttft * 1000), 'total_ms': round(elapsed * 1000)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "model": MAAS_MODEL, "gateway": MAAS_GATEWAY}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    print(f"\n  Fed Aura Capital AI Advisor")
    print(f"  http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
