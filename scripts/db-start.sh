#!/usr/bin/env bash
# Start local PostgreSQL via Docker Compose
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d postgres
echo "Waiting for postgres…"
until docker compose exec -T postgres pg_isready -U fmo -q; do sleep 1; done
echo "PostgreSQL ready at localhost:5432"
