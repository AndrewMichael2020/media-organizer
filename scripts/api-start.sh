#!/usr/bin/env bash
# Start the FastAPI development server
set -euo pipefail
# Ensure ~/.local/bin (exiftool) and /usr/local/bin are on PATH
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/apps/api"
exec uv run uvicorn app.main:app \
  --reload \
  --reload-dir "$REPO_ROOT/apps/api" \
  --reload-dir "$REPO_ROOT/packages/vision" \
  --reload-dir "$REPO_ROOT/packages/models" \
  --reload-dir "$REPO_ROOT/packages/db" \
  --reload-dir "$REPO_ROOT/packages/media" \
  --reload-dir "$REPO_ROOT/packages/storage" \
  --reload-dir "$REPO_ROOT/prompts" \
  --host 0.0.0.0 \
  --port 8000
