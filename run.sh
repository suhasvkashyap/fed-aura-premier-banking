#!/usr/bin/env bash
set -euo pipefail

BLUE='\033[0;34m'
RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
NC='\033[0m'

cd "$(dirname "$0")"

PORT="${PORT:-8080}"

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

VENV_DIR=".venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    uv venv "${VENV_DIR}" --quiet 2>/dev/null || python3 -m venv "${VENV_DIR}"
fi

echo -e "${BLUE}Installing dependencies...${NC}"
uv pip install --quiet fastapi uvicorn httpx python-dotenv -p "${VENV_DIR}/bin/python" 2>/dev/null \
    || "${VENV_DIR}/bin/pip" install --quiet fastapi uvicorn httpx python-dotenv

echo ""
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  Fed Aura Capital — AI Financial Advisor${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${GREEN}App:${NC}        http://localhost:${PORT}"
echo -e "  ${GREEN}Model:${NC}      ${MAAS_MODEL:-gemma4}"
echo -e "  ${GREEN}Gateway:${NC}    ${MAAS_GATEWAY:-https://maas.apps.ocp.cloud.rhai-tmm.dev}"
echo ""
echo -e "  ${BLUE}Tip:${NC} Open Perses dashboard side-by-side to see metrics move"
echo -e "  ${BLUE}Tip:${NC} Run ${GOLD}./background_load.sh &${NC} for baseline traffic"
echo ""

"${VENV_DIR}/bin/python" app.py
