# Fed Aura Capital — AI Financial Advisor Demo

A live demo app showing RHOAI observability in action. Chat with a banking AI advisor backed by Gemma4 on the MaaS gateway while watching Perses dashboards update in real-time.

## Quick Start

```bash
# 1. Copy the example env file and add your API key
cp .env.example .env
# Edit .env and set MAAS_API_KEY (get from RHOAI Dashboard → Gen AI studio → API keys)

# 2. Launch the app
./run.sh

# 3. Open http://localhost:8080 in your browser
```

## Demo Setup (for presentations)

```bash
# Terminal 1: Start background load (creates baseline dashboard activity)
./background_load.sh &

# Terminal 2: Start the app
./run.sh
```

Arrange your screen: Fed Aura chatbot on the left, Perses dashboard (`Observe → Dashboards`) on the right.

## Suggested Demo Flow

1. Click **"Check my balance"** — model responds with account data
2. Type **"Show my last 5 transactions"** — model lists specific transactions
3. Type **"Am I eligible for a 30-year mortgage?"** — model evaluates based on credit score and income
4. Type **"How is my investment portfolio doing?"** — model summarizes holdings and YTD performance
5. Point to Perses: *"Every message hit Gemma4 via llm-d. TTFT, token consumption, request throughput — all visible in real-time."*

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAAS_API_KEY` | (required) | Bearer token from RHOAI Dashboard |
| `MAAS_GATEWAY` | `https://maas.apps.ocp.cloud.rhai-tmm.dev` | MaaS gateway URL |
| `MAAS_MODEL` | `gemma4` | Model name |
| `MAX_TOKENS` | `512` | Max response tokens |
| `PORT` | `8080` | Local server port |

## Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI backend — proxies chat to MaaS gateway with streaming |
| `index.html` | Bank portal chatbot UI — navy/gold branding |
| `bank_data.py` | Synthetic customer data injected into system prompt |
| `background_load.sh` | Sends steady banking questions for dashboard baseline |
| `run.sh` | One-command launcher |
