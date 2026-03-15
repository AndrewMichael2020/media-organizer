# Media Archive Tool

<!-- OSINT / Forensic Intent -->
[![OSINT-Style Analysis](https://img.shields.io/badge/OSINT--Style-Image%20Analysis-8B0000?style=flat-square&logo=target&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Forensic Metadata](https://img.shields.io/badge/Forensic-Metadata%20Extraction-2F4F4F?style=flat-square&logo=files&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![AI-Powered](https://img.shields.io/badge/AI--Powered-Multimodal%20Extraction-7B2FBE?style=flat-square&logo=google&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Local-First](https://img.shields.io/badge/Local--First-No%20Cloud%20Required-228B22?style=flat-square&logo=homeassistant&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Originals Untouched](https://img.shields.io/badge/Originals-Never%20Moved%20or%20Copied-FF8C00?style=flat-square&logo=lock&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)

<!-- Backend Stack -->
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/latest/)
[![SQLAlchemy 2](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-6BA539?style=flat-square&logo=alembic&logoColor=white)](https://alembic.sqlalchemy.org/)

<!-- Frontend Stack -->
[![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

<!-- AI & Deterministic Tools -->
[![Gemini Flash-Lite](https://img.shields.io/badge/Gemini-Flash--Lite%20(default)-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![LM Studio](https://img.shields.io/badge/LM%20Studio-Local%20Inference-8A2BE2?style=flat-square&logo=ollama&logoColor=white)](https://lmstudio.ai/)
[![ExifTool](https://img.shields.io/badge/ExifTool-Metadata-DAA520?style=flat-square&logo=files&logoColor=white)](https://exiftool.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Video%20%2F%20Audio-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

<!-- Engineering Practices -->
[![Typed Schemas](https://img.shields.io/badge/Typed-Pydantic%20Schemas-E92063?style=flat-square&logo=checkmarx&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Idempotent Pipelines](https://img.shields.io/badge/Pipelines-Idempotent%20%26%20Restartable-F59E0B?style=flat-square&logo=apacheairflow&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Evidence Trail](https://img.shields.io/badge/Evidence-Full%20Extraction%20Trail-8B4513?style=flat-square&logo=microscope&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Reprocessing](https://img.shields.io/badge/Reprocessing-First--Class%20Feature-1E90FF?style=flat-square&logo=refresh&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![macOS](https://img.shields.io/badge/Primary%20Target-macOS-000000?style=flat-square&logo=apple&logoColor=white)](https://www.apple.com/macos/)

---

Local-first archive software for large personal photo collections.

The originals stay where they already live on disk. The app layers metadata, thumbnails, OCR, AI summaries, tags, places, and review queues on top so you can browse and search a big archive without reorganizing the files themselves.

## What It Does

- Scans folders recursively and keeps a catalog of the files it finds
- Extracts deterministic metadata with `exiftool` and `ffprobe`
- Generates thumbnails for common image, video, RAW, and Apple formats
- Runs AI extraction for OCR, summaries, tags, objects, place clues, and image notes
- Provides a local web app with Gallery, Places, Review, Jobs, and Settings
- Supports folder-scoped jobs so you can process one part of the archive at a time
- Has local model inferencing options for image analysis to reduce AI costs and latency

## What It Does NOT Do

- Runs on MacOS as a native app (but the web UI is designed for local use)
- Syncs or manages files on disk (it catalogs and layers metadata only)
- Provides a mobile app (but the web UI is responsive)
- Supports multi-user access or cloud deployment (but the API could be adapted for that in the future)
- Has CI/CD for cloud deployment (but the stack is containerized and could be adapted for that in the future; PostgrSQL was a poor choice))
- Has ideal UI/UX (but it is designed to be practical and iteratively improved)
- Has face detection (but it has people recognition and general object detection pipeline; face detection is next stage)
- Has image series deep analysis
- Map intelligence beyond basic reverse geocoding (but it extracts GPS and has a Places view for geo-tagged items)
- Web search and image reverse web search integrations (but it has local search over metadata and AI-generated tags and summaries)

## Current Focus

This project is optimized for local archive exploration, not cloud multi-user deployment.

- Primary development target: macOS
- Web UI: Next.js
- API: FastAPI
- Database: PostgreSQL via Docker
- AI provider: Gemini

### Gallery view
![Gallery view](public/image.png)

### Image card
![Image card](public/image-1.png)

### Image analysis
![Image analysis](public/image-2.png)

### Spacial analysis
![Spacial analysis](public/image-3.png)

### Jobs (pick AI model local or remote)
![Jobs (pick local or remote AI model)](public/image-4.png)

### Settings (enumerate folder, delete all artifact repos, etc.)

![Settings (enumerate folder, delete all artifact repos, etc.)](public/image-5.png)

## Requirements

- macOS or Linux 
- Docker Desktop
- `uv`
- Node.js 20+
- `exiftool`
- `ffmpeg`

Example install on macOS:

```bash
brew install uv exiftool ffmpeg
```

## Quick Start

1. Copy the example files.

```bash
cp .env.example .env
cp config/local.yaml.example config/local.yaml
```

2. Edit `config/local.yaml` and set your photo roots.

```yaml
storage:
  source_roots:
    - "/Users/you/Pictures"
```

3. Edit `.env` and add your Gemini key.

```bash
GEMINI_API_KEY=your_key_here
```

4. Start the stack.

```bash
bash scripts/dev.sh
```

That starts:

- PostgreSQL on `localhost:5432`
- API on `http://localhost:8000`
- Web app on `http://localhost:3000`

## Running Services Manually

```bash
bash scripts/db-start.sh
bash scripts/api-start.sh
bash scripts/web-start.sh
```

Useful URLs:

- Web UI: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Typical Workflow

1. Add one or more archive roots in Settings or `config/local.yaml`.
2. Run a scan.
3. Run enrich.
4. Run reprocess to generate thumbnails.
5. Run extract for AI metadata.
6. Browse in Gallery, inspect on the asset page, use Places for geo-tagged items, and use Review for items that need attention.

You can run jobs for the whole archive or for a selected folder only.

## Jobs

The Jobs page can run:

- `scan`
- `enrich`
- `reprocess`
- `extract`
- folder-level metadata reset

The app also supports stopping a queued or running job. Stop is cooperative: it stops between items rather than killing the current file mid-processing.

## Configuration

Defaults live in `config/default.yaml`.

Local machine overrides live in `config/local.yaml`.

Environment variables in `.env` can override config values too.

Important settings:

```yaml
database:
  url: "postgresql://fmo:fmo@localhost:5432/fmo"

model:
  provider: "gemini"
  name: "gemini-2.0-flash-lite"

storage:
  source_roots: []
  derivative_cache_root: "/tmp/fmo_cache"

worker:
  concurrency: 2
  image_analysis_max_px: 1200
  ai_max_output_tokens: null
```

Notes:

- `ai_max_output_tokens: null` means the app does not force an output cap.
- Set a numeric cap only if you intentionally want to limit output length.
- Keep secrets like API keys in `.env`, not in YAML config.

## Search

Gallery supports:

- broad text search
- structured scene, place, object, and AI-text filters
- folder browsing
- OCR and GPS filters
- review-state filters

The AI text search is useful for full-text matching over AI summaries, notes, and extracted text-like fields.

## Formats and Media Notes

### RAW / NEF

RAW support is practical but not perfect.

- The app prefers embedded previews for better thumbnails when available
- Some RAW files still produce soft previews if the embedded preview is missing or small
- For large RAW-heavy collections, rerun `reprocess` after updates that improve thumbnail handling

### HEIC / HEIF

Apple image formats are supported.

- On macOS, the app can fall back to `sips` when direct decoding is unreliable
- If HEIC files were ingested before those fixes, rerun `reprocess` and then `extract`

## AI Cost Guidance

For a large archive, cost control matters.

Practical ways to keep cost down:

- process by folder instead of the whole archive
- run deterministic enrichment and thumbnails first
- reserve AI extraction for folders you care about most
- reduce `image_analysis_max_px` before adding complicated extra prompts
- use a two-pass workflow later if you want a cheap broad pass and a richer selective pass

Very low budgets for fully detailed multimodal extraction across tens of thousands of images are usually unrealistic without a selective pipeline.

## Debugging AI Extraction

When AI extraction runs, debug payloads are written locally to:

`var/ai_debug`

These files are intentionally git-ignored. They are useful for inspecting raw model output when a parse or provider issue happens.

## Repo Layout

```text
apps/
  api/        FastAPI backend
  web/        Next.js frontend
  worker/     worker-side app code

packages/
  db/         database models, migrations, repositories
  media/      exiftool, ffmpeg, thumbnails, enrichment
  models/     provider adapters and schemas
  ocr/        OCR helpers
  search/     search helpers
  storage/    filesystem integration
  vision/     AI extraction orchestration

config/       default and local YAML config
prompts/      AI prompts
scripts/      local dev scripts
tests/        test code
```

## Notes for Contributors

- Do not commit real media.
- Do not commit `config/local.yaml` or `.env`.
- Do not commit `var/` contents.
- Treat this as a local archive app first: practical, fast, and inspectable beats overengineering.
