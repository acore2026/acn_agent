#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
export PIP_DISABLE_PIP_VERSION_CHECK=1

if [[ -f "${VENV_DIR}/bin/activate" ]]; then
  source "${VENV_DIR}/bin/activate"
  PYTHON_BIN="python"
elif python3 -m venv "${VENV_DIR}" >/dev/null 2>&1; then
  source "${VENV_DIR}/bin/activate"
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt"

cd "${ROOT_DIR}"
rm -rf build dist

"${PYTHON_BIN}" -m PyInstaller \
  --onefile \
  --name acn_agent \
  --paths "${ROOT_DIR}" \
  --collect-submodules acn_agent \
  acn_agent.py

echo "Executable generated: ${ROOT_DIR}/dist/acn_agent"
