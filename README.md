# Forensic Media Organizer

A private local-first forensic-grade media organizer for large photo and video archives.

Originals stay in place. Metadata, thumbnails, and AI-extracted knowledge are stored separately. Built for one user, on localhost, with a fast inspection-first UI.

---

## Prerequisites

- macOS (primary target: M1 Max)
- Docker Desktop (for PostgreSQL)
- [uv](https://docs.astral.sh/uv/) — Python package manager (`brew install uv`)
- Node.js 20+ and npm
- ExifTool (`brew install exiftool`)
- ffmpeg + ffprobe (`brew install ffmpeg`)

---

## Local setup

```bash
# 1. Copy config and env
cp config/local.yaml.example config/local.yaml   # edit source_roots
cp .env.example .env                              # add GEMINI_API_KEY

# 2. Start everything (macOS — opens terminals)
bash scripts/dev.sh
```

Or start services individually:

```bash
bash scripts/db-start.sh   # PostgreSQL via Docker
bash scripts/api-start.sh  # FastAPI on :8000
bash scripts/web-start.sh  # Next.js on :3000
```

---

## URLs

| Service | URL |
|---|---|
| Web UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| API health | http://localhost:8000/health |

---

## Project layout

```
apps/
  api/        FastAPI — catalog API and orchestration
  web/        Next.js — gallery, inspection, review, jobs, settings
  worker/     Background ingestion and extraction jobs

packages/
  core/       Domain models, config, shared schemas
  db/         Migrations, repositories
  media/      ExifTool / ffprobe / thumbnail wrappers
  models/     Multimodal model router and provider adapters
  ocr/        OCR normalization
  vision/     Extraction orchestration
  search/     Search and ranking
  storage/    Local filesystem adapter

config/       YAML config (default.yaml + local.yaml)
prompts/      Prompt templates (outside business logic)
scripts/      Dev and operational scripts
```

---

## Configuration

Edit `config/local.yaml` to set your source roots and model:

```yaml
storage:
  source_roots:
    - /path/to/your/photos

model:
  name: gemini-2.0-flash-lite
```

All values can also be overridden with `FMO_` env vars (e.g. `FMO_MODEL_NAME`).

---

## Restarting the servers

The stack runs as three separate processes: Docker (Postgres), FastAPI, and Next.js.
Each has its own terminal tab opened by `scripts/dev.sh`.

### Stop everything
```bash
# Stop Docker
docker compose down

# Kill API (find the uvicorn PID and kill it)
lsof -ti :8000 | xargs kill -9

# Kill Next.js dev server
lsof -ti :3000 | xargs kill -9
```

### Restart individual servers
```bash
# API only (picks up Python changes automatically via --reload)
bash scripts/api-start.sh

# Web only (Next.js hot-reloads automatically, but full restart if needed)
bash scripts/web-start.sh

# DB only (normally stays running between restarts)
bash scripts/db-start.sh
```

### Restart everything fresh
```bash
bash scripts/dev.sh
```

> **Note:** The FastAPI server (`--reload`) and Next.js dev server both support **hot reload** —
> most code changes are picked up automatically without a restart.
> You only need to restart if you add new Python packages (`uv add`) or change `next.config.ts`.

## Commands

### Python packages
```bash
# Run DB migrations
bash scripts/db-migrate.sh

# Scan a source root (via API)
curl -X POST http://localhost:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"scan","source_root":"/path/to/photos"}'

# Enrich all pending assets (ExifTool + ffprobe)
curl -X POST http://localhost:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"enrich"}'

# Generate thumbnails
curl -X POST http://localhost:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"reprocess"}'

# AI extraction (requires GEMINI_API_KEY in .env)
curl -X POST http://localhost:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '{"type":"extract"}'
```

## What's implemented

- [x] Monorepo scaffold (Issue 1.1)
- [x] YAML + env config system (Issue 1.2)
- [x] Dev scripts: `scripts/dev.sh`, `api-start.sh`, `web-start.sh`, `db-migrate.sh` (Issue 1.3)
- [x] FastAPI: `/health`, `/assets`, `/jobs`, `/jobs/ingest`, `/config` — wired to real DB
- [x] Next.js app shell — Gallery, Places, Review, Jobs, Settings — wired to real API
- [x] White-first artsy UI (sidebar nav, topbar, theme switch, masonry grid, list view, filters)
- [x] PostgreSQL schema: 16 tables with indexes (Issue 2.1)
- [x] Alembic migrations (`packages/db/migrations/`)
- [x] DB session factory (`packages/db/session.py`)
- [x] Asset repository — upsert, list, mark-missing (Issue 2.2 partial)
- [x] Filesystem scanner — recursive scan, delta detection (Issue 3.1–3.2)
- [x] SHA-256 + pHash hashing (Issue 3.3)
- [x] ExifTool adapter (Issue 4.1 partial)
- [x] ffprobe adapter (Issue 4.1 partial)
- [x] Deterministic enrichment — media info, temporal resolution, GPS location (Issue 4.1–4.2)
- [x] Scan + enrich + thumbnail + AI extract jobs wired to FastAPI background tasks (Issue 7.1)
- [x] Source root picker in Settings — typed path, live validation, one-click scan
- [x] Thumbnail generation — PIL resize for images, ffmpeg keyframes for video (Issue 4.3)
- [x] `GET /assets/{id}/thumbnail` — serve thumbnail JPEG, fallback to keyframe
- [x] Asset detail page `/asset/[id]` — OCR, scene, objects, place candidates, raw EXIF
- [x] Model router + Gemini adapter (`packages/models/`) (Issue 5.1)
- [x] Extraction schemas + `prompts/image_v1.txt` (Issues 5.2–5.3)
- [x] AI image extraction pipeline — validate → persist OCR/scene/objects/places (Issue 6.1–6.3)
- [x] Full-text search wired in gallery filter bar (Issue 8.2)

## What's next

- [ ] Review queues UI (Issue 9.4)
- [ ] Places page — map or list of geo-tagged assets (Issue 9.5)
- [ ] Video extraction — keyframe-level AI extraction (Issue 6.4)
- [ ] Person region persistence + clustering (Issue 6.2)
- [ ] Full Assertion audit trail UI (Issue 10.x)
