# Media Archive Tool

Local-first archive software for large personal photo collections.

The originals stay where they already live on disk. The app layers metadata, thumbnails, OCR, AI summaries, tags, places, and review queues on top so you can browse and search a big archive without reorganizing the files themselves.

## What It Does

- Scans folders recursively and keeps a catalog of the files it finds
- Extracts deterministic metadata with `exiftool` and `ffprobe`
- Generates thumbnails for common image, video, RAW, and Apple formats
- Runs AI extraction for OCR, summaries, tags, objects, place clues, and image notes
- Provides a local web app with Gallery, Places, Review, Jobs, and Settings
- Supports folder-scoped jobs so you can process one part of the archive at a time
- Supports local model inferencing

## What It Does Not Do

- Runs on MacOS as a native app (but the web UI is designed for local use)
- Syncs or manages files on disk (it catalogs and layers metadata only)
- Provides a mobile app (but the web UI is responsive)
- Supports multi-user access or cloud deployment (but the API could be adapted for that in the future)
- Has CI/CD for cloud deployment (but the stack is containerized and could be adapted for that in the future)
- Has ideal UI/UX (but it is designed to be practical and iteratively improved)

## Current Focus

This project is optimized for local archive exploration, not cloud multi-user deployment.

- Primary development target: macOS
- Web UI: Next.js
- API: FastAPI
- Database: PostgreSQL via Docker
- AI provider: Gemini

![Gallery view](public/image.png)

![Image card](public/image-1.png)

![Image analysis](public/image-2.png)

![Spacial analysis](public/image-3.png)

![Jobs (pick local or remote AI model)](public/image-4.png)

![Settings (enumerate folder, delete all artifact repos, etc.)](public/image-5.png)

## Requirements

- macOS
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
