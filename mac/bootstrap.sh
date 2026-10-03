#!/bin/bash
# Create the local Python environment used by the install and restore commands.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x "$ROOT/.venv/bin/python3" ]; then
  python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/python3" -m pip install -q -r "$ROOT/requirements.txt"
