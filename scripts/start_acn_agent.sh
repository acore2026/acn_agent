#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/requirements.txt"

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

EXISTING_PIDS="$(pgrep -f "python3 ${ROOT_DIR}/acn_agent.py" || true)"
if [[ -n "${EXISTING_PIDS}" ]]; then
  echo "Stopping existing ACN Agent process: ${EXISTING_PIDS}"
  kill ${EXISTING_PIDS}
  sleep 1
fi

exec python3 "${ROOT_DIR}/acn_agent.py"
