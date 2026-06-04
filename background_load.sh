#!/usr/bin/env bash
set -euo pipefail

# Fed Aura Capital — Background Load Generator
# Sends banking-themed questions to Gemma4 every 5-10 seconds.
# Creates a steady baseline on the Perses dashboard so live chat
# requests produce visible spikes on top of it.
#
# Usage: ./background_load.sh &
# Kill:  kill %1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

MAAS_GATEWAY="${MAAS_GATEWAY:-https://maas.apps.ocp.cloud.rhai-tmm.dev}"
MAAS_MODEL="${MAAS_MODEL:-gemma4}"
MAAS_API_KEY="${MAAS_API_KEY:-}"
INTERVAL="${INTERVAL:-7}"

ENDPOINT="${MAAS_GATEWAY}/prelude-maas/${MAAS_MODEL}/v1/chat/completions"

if [ -z "${MAAS_API_KEY}" ]; then
    echo "[bg-load] ERROR: MAAS_API_KEY is not set."
    echo "  Add it to .env or: export MAAS_API_KEY=<your-api-key>"
    exit 1
fi

PROMPTS=(
    "What is my checking account balance?"
    "Show my recent transactions."
    "What mortgage rates do you currently offer?"
    "How is my investment portfolio performing this year?"
    "Where is the nearest Fed Aura branch?"
    "What are your savings account interest rates?"
    "Am I eligible for a personal loan?"
    "What is my credit score?"
    "How much did I spend on groceries this month?"
    "Can you help me set up automatic transfers to savings?"
    "What are the hours for the Financial District branch?"
    "Tell me about your home equity line of credit."
    "What is my total net worth across all accounts?"
    "How does my portfolio allocation compare to the benchmark?"
    "What auto loan rates do you offer for new vehicles?"
)

echo "[bg-load] Fed Aura Capital background traffic"
echo "[bg-load] Endpoint: ${ENDPOINT}"
echo "[bg-load] Interval: ~${INTERVAL}s between requests"
echo "[bg-load] Kill with: kill $$"
echo ""

IDX=0
while true; do
    PROMPT="${PROMPTS[$((IDX % ${#PROMPTS[@]}))]}"
    MAX_T=$(( (RANDOM % 80) + 30 ))

    HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 30 \
        -H "Authorization: Bearer ${MAAS_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ENDPOINT}" \
        -d "{
            \"model\": \"${MAAS_MODEL}\",
            \"messages\": [
                {\"role\": \"system\", \"content\": \"You are a bank's AI assistant. Answer briefly.\"},
                {\"role\": \"user\", \"content\": \"${PROMPT}\"}
            ],
            \"max_tokens\": ${MAX_T}
        }" 2>/dev/null || echo "000")

    TIMESTAMP=$(date +%H:%M:%S)
    echo "[bg-load] ${TIMESTAMP} | ${HTTP_CODE} | ${PROMPT:0:50}"

    IDX=$((IDX + 1))
    JITTER=$(( (RANDOM % 6) - 2 ))
    SLEEP=$(( INTERVAL + JITTER ))
    [ "${SLEEP}" -lt 3 ] && SLEEP=3
    sleep "${SLEEP}"
done
