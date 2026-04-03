#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PID_FILE="${ROOT_DIR}/.acn_agent.pid"
LOG_FILE="${ROOT_DIR}/.acn_agent.log"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/requirements.txt"

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

stop_pid() {
  local pid="$1"
  if kill -0 "${pid}" 2>/dev/null; then
    echo "Stopping existing ACN Agent process: ${pid}"
    kill "${pid}" 2>/dev/null || true
    for _ in {1..10}; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        return 0
      fi
      sleep 1
    done
    kill -9 "${pid}" 2>/dev/null || true
  fi
}

if [[ -f "${PID_FILE}" ]]; then
  OLD_PID="$(<"${PID_FILE}")"
  if [[ "${OLD_PID}" =~ ^[0-9]+$ ]]; then
    stop_pid "${OLD_PID}"
  fi
  rm -f "${PID_FILE}"
fi

while IFS= read -r pid; do
  [[ -n "${pid}" ]] || continue
  stop_pid "${pid}"
done < <(pgrep -f "python3 .*acn_agent.py" || true)

nohup python3 "${ROOT_DIR}/acn_agent.py" >"${LOG_FILE}" 2>&1 &
NEW_PID="$!"
echo "${NEW_PID}" > "${PID_FILE}"

echo "ACN Agent started in background: ${NEW_PID}"
echo "Log file: ${LOG_FILE}"
