#!/usr/bin/env bash
set -euo pipefail

BLUE='\033[0;34m'
RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
DIM='\033[2m'
NC='\033[0m'

cd "$(dirname "$0")"

# Source .env for variables used in the banner
if [ ! -f .env ]; then
    echo -e "${RED}ERROR:${NC} .env file not found."
    echo ""
    echo "  1. Copy the example:  cp .env.example .env"
    echo "  2. Edit .env and set your MAAS_API_KEY"
    echo "  3. Run:  ./run.sh"
    echo ""
    exit 1
fi

if grep -q "your-api-key-here" .env 2>/dev/null; then
    echo -e "${RED}ERROR:${NC} MAAS_API_KEY is still the placeholder value in .env"
    echo "  Edit .env and set your real API key."
    exit 1
fi

set -a; source .env; set +a

PORT="${PORT:-8080}"
MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-http://localhost:5000}"

VENV_DIR=".venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    uv venv "${VENV_DIR}" --quiet 2>/dev/null || python3 -m venv "${VENV_DIR}"
fi

echo -e "${BLUE}Installing dependencies...${NC}"
uv pip install --quiet fastapi uvicorn httpx python-dotenv mlflow -p "${VENV_DIR}/bin/python" 2>/dev/null \
    || "${VENV_DIR}/bin/pip" install --quiet fastapi uvicorn httpx python-dotenv mlflow

# Start local MLflow server if tracking URI points to localhost
MLFLOW_PID=""
if [[ "${MLFLOW_TRACKING_URI}" == *"localhost"* ]] || [[ "${MLFLOW_TRACKING_URI}" == *"127.0.0.1"* ]]; then
    MLFLOW_PORT=$(echo "${MLFLOW_TRACKING_URI}" | grep -o '[0-9]*$')
    MLFLOW_PORT="${MLFLOW_PORT:-5000}"

    if ! curl -s -o /dev/null --max-time 2 "${MLFLOW_TRACKING_URI}/health" 2>/dev/null; then
        echo -e "${BLUE}Starting local MLflow server on port ${MLFLOW_PORT}...${NC}"
        "${VENV_DIR}/bin/mlflow" server \
            --host 127.0.0.1 \
            --port "${MLFLOW_PORT}" \
            --artifacts-destination ./mlruns \
            > /dev/null 2>&1 &
        MLFLOW_PID=$!
        sleep 2
    else
        echo -e "${DIM}MLflow server already running on port ${MLFLOW_PORT}${NC}"
    fi
fi

cleanup() {
    if [ -n "${MLFLOW_PID}" ]; then
        kill "${MLFLOW_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo ""
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  Fed Aura Capital — AI Financial Advisor${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${GREEN}App:${NC}        http://localhost:${PORT}"
echo -e "  ${GREEN}MLflow:${NC}     ${MLFLOW_TRACKING_URI}"
echo -e "  ${GREEN}Model:${NC}      ${MAAS_MODEL:-gemma4}"
echo ""
echo -e "  ${BLUE}Tip:${NC} Open the Perses dashboard and MLflow UI side-by-side"
echo -e "  ${BLUE}Tip:${NC} Run ${GOLD}./background_load.sh &${NC} for baseline Perses traffic"
echo ""

"${VENV_DIR}/bin/python" app.py
