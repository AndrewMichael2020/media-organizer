#!/usr/bin/env bash
# Start the Next.js development server
set -euo pipefail
cd "$(dirname "$0")/../apps/web"
exec npm run dev
