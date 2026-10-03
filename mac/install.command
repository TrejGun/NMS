#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"

bash "$DIR/bootstrap.sh"
status=$?
if [ "$status" -eq 0 ]; then
  "$ROOT/.venv/bin/python3" -m nmsfix install
  status=$?
fi

echo
printf "Press Return to close this window. "
read -r _
exit "$status"
