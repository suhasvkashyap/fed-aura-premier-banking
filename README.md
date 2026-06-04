# Fed Aura Capital — AI Financial Advisor Demo

A live demo app showing RHOAI observability in action. Chat with a banking AI advisor backed by Gemma4 on the MaaS gateway while watching both **Perses dashboards** (infrastructure metrics) and **MLflow traces** (application-level debugging) update in real-time.

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
6. Switch to MLflow UI (`http://localhost:5000`) — *"Now look at the application layer. Every chat message created a trace. I can see the exact prompt, the full response, token counts, and latency. If something went wrong, I trace it here."*

## MLflow Tracing

Every chat message automatically creates an MLflow trace under the **"Fed Aura Capital"** experiment. No extra setup needed — `run.sh` starts a local MLflow server alongside the app.

**What each trace shows:**
- **Root span** (`fed-aura-chat`): the user's question and the full assistant response
- **Child span** (`llm-inference`): the model call with prompt tokens, completion tokens, TTFT, total latency, and model name

**How to view traces:**
1. Open `http://localhost:5000` in your browser
2. Click the **"Fed Aura Capital"** experiment
3. Click **Traces** tab to see all chat interactions
4. Click any trace to see the full span tree, inputs, outputs, and token usage

**Two observability layers in one demo:**

| Layer | Tool | What it shows | Who cares |
|-------|------|--------------|-----------|
| Infrastructure | Perses | TTFT, throughput, GPU utilization, queue depth, token consumption | Platform SRE |
| Application | MLflow | Prompt/response content, per-request tokens, latency, trace tree | ML Engineer |

**Note:** Background load (`background_load.sh`) only populates Perses — it hits vLLM directly via curl, bypassing the app. This is intentional: it demonstrates that Perses captures all platform traffic while MLflow only traces application-instrumented requests.

## Sample Questions

Sarah Chen is a Premier Banking customer. The model has her full profile loaded, so these questions all return specific, data-grounded answers.

### Account Balances
- What is my checking account balance?
- How much do I have across all my accounts?
- What is the interest rate on my savings account?
- What is my total net worth at Fed Aura?

### Transactions
- Show me my last 5 transactions
- How much did I spend on groceries this month?
- When was my last paycheck deposited and how much was it?
- Did I make any transfers recently?
- How much am I paying for subscriptions like Netflix and the gym?

### Loans & Mortgage
- What mortgage rates do you currently offer?
- Am I eligible for a 30-year fixed mortgage?
- How much house could I afford based on my income?
- What is the difference between your 15-year and 30-year mortgage rates?
- Do you offer personal loans? What are the terms?
- What auto loan rates do you have for a new car?

### Investment Portfolio
- How is my investment portfolio performing?
- What is my asset allocation?
- Which of my holdings has performed best this year?
- What percentage of my portfolio is in stocks vs bonds?
- How much have I gained this year in my investment account?
- Tell me about my Bitcoin ETF position

### Financial Planning
- I'm paying $3,200 in rent. Should I consider buying a home?
- How much should I be saving each month?
- Can you summarize my overall financial picture?
- I want to increase my emergency fund. How much do I have in savings?

### Branch & Support
- Where is the nearest branch to me?
- What are the hours for the Financial District branch?
- Is there a branch open on Saturdays?
- Do you have a branch in Palo Alto?
- How many fee-free ATMs do you have?

### Multi-Turn Conversations (follow-ups)

These show the model retaining context across messages:

1. "What is my checking balance?" → "And my savings?" → "So what is my total across both?"
2. "What mortgage rates do you offer?" → "Am I eligible?" → "How much would my monthly payment be on a $600,000 home?"
3. "How is my portfolio doing?" → "Which holding is the weakest?" → "Should I be concerned about my bond allocation?"

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAAS_API_KEY` | (required) | Bearer token from RHOAI Dashboard |
| `MAAS_GATEWAY` | (set in .env) | MaaS gateway URL |
| `MAAS_MODEL` | `gemma4` | Model name |
| `MAX_TOKENS` | `512` | Max response tokens |
| `PORT` | `8080` | Local server port |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow server URL (local or remote) |
| `MLFLOW_EXPERIMENT_NAME` | `Fed Aura Capital` | MLflow experiment name |

## Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI backend — proxies chat to MaaS gateway with streaming |
| `index.html` | Bank portal chatbot UI — navy/gold branding |
| `bank_data.py` | Synthetic customer data injected into system prompt |
| `background_load.sh` | Sends steady banking questions for dashboard baseline |
| `run.sh` | One-command launcher |
