#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PID_FILE="${ROOT_DIR}/.acn_agent.pid"
LOG_FILE="${ROOT_DIR}/.acn_agent.log"
DEPS_READY_FILE="${VENV_DIR}/.deps_ready"

stop_pid() {
  local pid="$1"
  if ! kill -0 "${pid}" 2>/dev/null; then
    return 1
  fi

  echo "Stopping existing ACN Agent process: ${pid}"
  kill "${pid}" 2>/dev/null || true
  for _ in {1..10}; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  kill -9 "${pid}" 2>/dev/null || true
}

setup_env() {
  local created_venv=0
  if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
    created_venv=1
  fi

  source "${VENV_DIR}/bin/activate"

  if [[ "${created_venv}" -eq 1 || ! -f "${DEPS_READY_FILE}" ]]; then
    echo "Installing ACN Agent Python dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -r "${ROOT_DIR}/requirements.txt"
    touch "${DEPS_READY_FILE}"
  else
    echo "ACN Agent Python dependencies already prepared."
  fi

  export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
}

pid_from_file() {
  if [[ -f "${PID_FILE}" ]]; then
    local pid
    pid="$(<"${PID_FILE}")"
    if [[ "${pid}" =~ ^[0-9]+$ ]]; then
      echo "${pid}"
    fi
  fi
}

is_running() {
  local pid="$1"
  kill -0 "${pid}" 2>/dev/null
}

find_agent_pid() {
  pgrep -f "python3 .*acn_agent.py" 2>/dev/null | head -n 1 || true
}

start_agent() {
  local old_pid
  old_pid="$(pid_from_file || true)"

  if [[ -n "${old_pid}" ]] && is_running "${old_pid}"; then
    echo "ACN Agent is already running: ${old_pid}"
    echo "Log file: ${LOG_FILE}"
    return 0
  fi

  old_pid="$(find_agent_pid)"
  if [[ -n "${old_pid}" ]] && is_running "${old_pid}"; then
    echo "${old_pid}" > "${PID_FILE}"
    echo "ACN Agent is already running: ${old_pid}"
    echo "Log file: ${LOG_FILE}"
    return 0
  fi

  rm -f "${PID_FILE}"
  setup_env

  nohup python3 "${ROOT_DIR}/acn_agent.py" >"${LOG_FILE}" 2>&1 &
  local new_pid="$!"
  echo "${new_pid}" > "${PID_FILE}"

  echo "ACN Agent started in background: ${new_pid}"
  echo "Log file: ${LOG_FILE}"
}

stop_agent() {
  local stopped=0
  local old_pid
  old_pid="$(pid_from_file || true)"

  if [[ -n "${old_pid}" ]]; then
    if stop_pid "${old_pid}"; then
      stopped=1
    fi
  fi
  rm -f "${PID_FILE}"

  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    if stop_pid "${pid}"; then
      stopped=1
    fi
  done < <(pgrep -f "python3 .*acn_agent.py" || true)

  if [[ "${stopped}" -eq 0 ]]; then
    echo "ACN Agent is not running"
  else
    echo "ACN Agent stopped"
  fi
}

restart_agent() {
  stop_agent
  start_agent
}

show_log() {
  touch "${LOG_FILE}"
  echo "Following ACN Agent log: ${LOG_FILE}"
  tail -f "${LOG_FILE}"
}

usage() {
  cat <<EOF
Usage: $0 {start|stop|restart|log}

Commands:
  start    Start ACN Agent in the background
  stop     Stop ACN Agent
  restart  Stop then start ACN Agent
  log      Follow the ACN Agent log
EOF
}

COMMAND="${1:-start}"

case "${COMMAND}" in
  start)
    start_agent
    ;;
  stop)
    stop_agent
    ;;
  restart)
    restart_agent
    ;;
  log|logs)
    show_log
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
