#!/usr/bin/env bash
# One-command local stack start (runs each service in a new terminal tab on macOS)
set -euo pipefail
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"

bash "$SCRIPTS/db-start.sh"

API_SCRIPT="$SCRIPTS/api-start.sh"
WEB_SCRIPT="$SCRIPTS/web-start.sh"

osascript -e "tell application \"Terminal\" to do script \"bash '$API_SCRIPT'\""
osascript -e "tell application \"Terminal\" to do script \"bash '$WEB_SCRIPT'\""

echo ""
echo "Stack starting:"
echo "  API  → http://localhost:8000/docs"
echo "  Web  → http://localhost:3000"
