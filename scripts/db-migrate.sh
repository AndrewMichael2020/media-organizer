#!/usr/bin/env bash
# Run Alembic migrations against the configured database
set -euo pipefail
cd "$(dirname "$0")/../packages/db"
exec uv run alembic upgrade head
