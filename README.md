# Media Archive Tool

<!-- Intent -->
[![AI-Powered](https://img.shields.io/badge/AI--Powered-Multimodal%20Extraction-7B2FBE?style=flat-square&logo=google&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Local-First](https://img.shields.io/badge/Local--First-No%20Cloud%20Required-228B22?style=flat-square&logo=homeassistant&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)
[![Original Images Untouched](https://img.shields.io/badge/Originals-Never%20Moved%20or%20Copied-FF8C00?style=flat-square&logo=lock&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)

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
[![Grounded in Evidence](https://img.shields.io/badge/Evidence-Full%20Extraction%20Trail-8B4513?style=flat-square&logo=microscope&logoColor=white)](https://github.com/AndrewMichael2020/media-organizer)

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
- Has CI/CD for cloud deployment (but the stack is containerized and could be adapted for that in the future; PostgrSQL was a poor choice for local)
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
![Gallery view](public/image-0.png)

### Another Gallery view with filters open
![Gallery View](public/image-6.png)

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

## Shut the App Down

`kill -9 $(lsof -t -i:8000 -i:3000)`

Stop the db on local Docker: `docker compose down`

Option: stop all processes with `pkill -f "uv run"` or `pkill -f node python`

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

If the API server is interrupted or restarted while jobs are in progress, any `queued` or `running` jobs are marked `cancelled` on the next API startup so the UI does not keep showing stale running jobs forever.

### Batch extraction timing

`Gemini · gemini-2.5-flash-lite + Batch` is the lowest-cost cloud option in the app, but it is asynchronous.

What to expect:

- Small folder with a handful of images:
  often finishes within a few seconds to a couple of minutes, but it is not guaranteed to feel immediate
- Medium folder with dozens to a few hundred images:
  often takes minutes, and may vary based on current Gemini batch queue load
- Large archive batch:
  may take much longer and is best treated as background work rather than interactive processing

In this app, batch extraction currently waits for a reasonable short window. If Gemini batch does not finish in that window, the job falls back to direct `gemini-2.5-flash-lite` extraction with the same low-cost image profile instead of sitting in `running` forever.

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
  name: "gemini-3.1-flash-lite-preview"

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

Main Apple image formats are supported.

- On macOS, the app can fall back to `sips` when direct decoding is unreliable
- If HEIC files were ingested before those fixes, rerun `reprocess` and then `extract`

## AI Cost Guidance

This app can be run with several different AI cost profiles. The right choice depends on whether you care most about:

- best detail and stronger OCR
- lowest cloud cost
- local inference with no per-image API bill

### Important current caveat

OCR in the current pipeline is still largely model-side, not fully local. That means aggressive image downsizing can reduce cost, but it can also hurt tiny-text extraction.

Because of that, the app currently uses two practical image profiles:

- standard extraction:
  around `1200px` longest side with normal JPEG compression
- hyper-optimized extraction:
  around `768px` longest side with stronger JPEG compression, used for the Flash-Lite batch option

Use the hyper-optimized mode when you want lower cost and do **not** expect tiny text to be critical.

### Official provider pricing used by this repo

As of 2026-03-15, the codebase prices extraction using the current public provider pricing pages.

| Model / mode | Input per 1M tokens (USD) | Output per 1M tokens (USD) | Notes |
|---|---:|---:|---|
| Gemini 3.1 Flash-Lite Preview | 0.25 | 1.50 | richer but noticeably more expensive |
| Gemini 3.1 Flash-Lite Preview + Batch | 0.125 | 0.75 | same model, Batch API discount |
| Gemini 2.5 Flash | 0.15 | 1.25 | stronger than Lite, cheaper than 3.1 preview on output |
| Gemini 2.5 Flash + Batch | 0.075 | 0.625 | batch-discounted 2.5 Flash |
| Gemini 2.5 Flash-Lite | 0.10 | 0.40 | current low-cost cloud default for cheap runs |
| Gemini 2.5 Flash-Lite + Batch | 0.05 | 0.20 | cheapest hosted cloud option in the app |
| DeepInfra Llama 3.2 11B Vision | 0.049 total | 0.049 total | DeepInfra currently publishes a single per-token rate rather than separate input/output pricing |
| DeepInfra Llama 3.2 11B Vision (app batch) | 0.049 total | 0.049 total | app-side batching improves throughput, but does **not** create a provider-side token discount |
| LM Studio local models | 0.00 | 0.00 | no API bill, but you pay local hardware / electricity instead |

### Real token history from this repo

The following comes from the current extraction history in the local DB at the time this README was updated.

| Model seen in history | Successful runs | Avg input tokens / image | Avg output tokens / image | Avg cost / image (USD) |
|---|---:|---:|---:|---:|
| Gemini 3.1 Flash-Lite Preview | 31 | 2,579 | 1,247 | 0.002515 |
| Gemini 2.5 Flash-Lite | 2 | 2,214 | 1,802 | 0.000942 |

### Typical per-image cost scenarios from real runs

These are not guesses from a blog post. They are computed from the token patterns already observed in this archive.

#### Gemini 3.1 Flash-Lite Preview

| Scenario from history | Input tokens | Output tokens | Cost / image (USD) |
|---|---:|---:|---:|
| Average observed run | 2,579 | 1,247 | 0.002515 |
| P50 observed run | 2,913 | 1,341 | 0.002740 |
| P90 observed run | 2,961 | 1,645 | 0.003208 |

#### Gemini 2.5 Flash-Lite

| Scenario from history | Input tokens | Output tokens | Cost / image (USD) |
|---|---:|---:|---:|
| Average observed run | 2,214 | 1,802 | 0.000942 |
| Same token profile with Batch discount | 2,214 | 1,802 | 0.000471 |
| P50 observed run | 2,184 | 1,337 | 0.000753 |
| P90 observed run | 2,243 | 2,266 | 0.001131 |

#### DeepInfra Llama 3.2 11B Vision

DeepInfra pricing is currently published as a single `$0.049 / 1M tokens` rate for this model, so the estimates below use `(input + output) * 0.049 / 1,000,000`.

| Scenario from history | Input tokens | Output tokens | Cost / image (USD) |
|---|---:|---:|---:|
| Using Gemini 3.1 average token profile | 2,579 | 1,247 | 0.000187 |
| Using Gemini 3.1 P50 token profile | 2,913 | 1,341 | 0.000208 |
| Using Gemini 3.1 P90 token profile | 2,961 | 1,645 | 0.000226 |
| Using Gemini 2.5 Flash-Lite average token profile | 2,214 | 1,802 | 0.000197 |
| Using Gemini 2.5 Flash-Lite P50 token profile | 2,184 | 1,337 | 0.000173 |
| Using Gemini 2.5 Flash-Lite P90 token profile | 2,243 | 2,266 | 0.000221 |

These are **pricing estimates only**. DeepInfra may produce different token counts than Gemini for the same image and prompt, so you should expect some variance once you have real run history for that provider.

### Archive-scale cost scenarios

These tables use the real average token usage already seen in this repo.

| Images processed | Gemini 3.1 Flash-Lite Preview | Gemini 2.5 Flash-Lite | Gemini 2.5 Flash-Lite + Batch | DeepInfra Llama 3.2 11B Vision |
|---|---:|---:|---:|---:|
| 1,000 | 2.52 USD | 0.94 USD | 0.47 USD | 0.20 USD |
| 10,000 | 25.15 USD | 9.42 USD | 4.71 USD | 1.97 USD |
| 100,000 | 251.52 USD | 94.19 USD | 47.10 USD | 19.68 USD |

The DeepInfra column uses the observed Gemini 2.5 Flash-Lite average token profile (`2,214` input + `1,802` output) only as a proxy for comparison. Real DeepInfra runs may be somewhat higher or lower in total tokens.

### Practical recommendations

| Goal | Recommended mode | Why |
|---|---|---|
| Best current cloud detail | Gemini 3.1 Flash-Lite Preview | richer output, but most expensive |
| Cheap broad processing | Gemini 2.5 Flash-Lite | much lower cost with acceptable quality |
| Cheapest hosted cloud option in this app | Gemini 2.5 Flash-Lite + Batch | lowest token rates and lower-resolution image profile |
| Lowest hosted token price in the current model selector | DeepInfra Llama 3.2 11B Vision | very low published token rate; quality and token behavior should be evaluated on your own archive |
| Fast cheap cloud throughput without provider-side batch discounts | DeepInfra Llama 3.2 11B Vision (app batch) | app-side async concurrency and 100-image chunking improve throughput, but pricing is still the same per token |
| No API bill | LM Studio local models | useful if local quality is acceptable and you already have the hardware |

### Compression and resize guidance

The common advice to resize images to `768px` and use low-quality JPEGs is directionally correct, but in this app it must be used carefully.

#### Good use cases

- large archives where you mainly want scene summary, tags, and broad object clues
- folders where OCR is unlikely to matter
- inexpensive first-pass review

#### Risky use cases

- posters, signs, banners, bib numbers, storefronts, street signs
- screenshots or document-like photos
- historical images where tiny visible text matters

#### Recommendation for this repo

| Use case | Suggested setting |
|---|---|
| OCR-sensitive or detail-sensitive images | standard extraction profile |
| broad archive surfacing with cost pressure | Flash-Lite + Batch |
| future two-pass pipeline | cheap broad pass first, then rerun only selected assets in standard mode |

### Batch timing guidance

Batch is cheaper, but it is not instant.

Reasonable expectations:

| Batch size | What it often feels like |
|---|---|
| a handful of images | seconds to a couple of minutes |
| dozens to a few hundred images | minutes, depending on Gemini queue load |
| very large archive batches | background processing, not an interactive click-and-wait workflow |

The app currently waits a short window for batch completion. If Gemini batch does not finish in that window, the job falls back to direct `gemini-2.5-flash-lite` extraction with the same low-cost image profile instead of sitting in `running` forever.

### Theoretical exploration: Phi-family vision on GCP / Cloud Run

If you want to avoid per-image API costs entirely, you can explore self-hosting a Phi-family multimodal model. One important note: the exact model name `Phi-4-Reasoning-Vision (15B)` was not something this repo currently verifies as an official, clearly documented deployment target, so treat this section as a **theoretical exploration path** for a Phi-family vision-capable model rather than a drop-in supported option today.

#### Practical deployment shapes

| Option | Feasibility | Cost pattern | Operational burden | Notes |
|---|---|---|---|---|
| Cloud Run + GPU | possible in principle for a compact quantized multimodal Phi-family model | low idle overhead if scaled to zero, but GPU time is still expensive | medium | attractive for bursty testing; throughput and cold starts matter |
| GCE VM with GPU | straightforward if the model fits the chosen GPU | pay while VM is up | medium | easier to tune, easier to benchmark, better for long-running jobs |
| GKE / managed serving | strongest for large sustained pipelines | highest ops complexity | high | more appropriate if you outgrow this local-first archive app |

#### When a self-hosted Phi path makes sense

- you want predictable monthly infrastructure spend instead of API metering
- you have sustained enough volume to keep a GPU busy
- you are comfortable with model serving, container builds, and GPU ops

#### When it usually does **not** make sense

- small or occasional folders
- highly bursty use where the GPU would sit idle most of the time
- when you still need strong OCR and robust multimodal extraction out of the box

For this app today:

- `Gemini 2.5 Flash-Lite + Batch` is the simplest cheap hosted option with a real provider-side batch discount
- `DeepInfra Llama 3.2 11B Vision` is currently the lowest published hosted token price in the selector, but you should benchmark extraction quality on your own archive before treating it as a full replacement
- a self-hosted Phi-family path is interesting, but it is still a second-stage engineering project, not just a model dropdown

### Pricing references used in this section

- Google Gemini API pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- DeepInfra model pricing for `meta-llama/Llama-3.2-11B-Vision-Instruct`: `https://deepinfra.com/meta-llama/Llama-3.2-11B-Vision-Instruct`

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
