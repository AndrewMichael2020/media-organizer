#!/usr/bin/env bash
# Start the FastAPI development server
set -euo pipefail
# Ensure ~/.local/bin (exiftool) and /usr/local/bin are on PATH
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/../apps/api"
exec uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
