# GitHub Copilot Instructions — Forensic Media Organizer

## Product intent

A **local-first, single-user forensic media organizer** for a large private archive of photos and videos. This is not a consumer gallery. It is a metadata-and-evidence system that:

- leaves originals in place
- extracts rich structured metadata via multimodal AI and deterministic tools
- stores derived artifacts separately from originals
- supports fast search, inspection, review, and reprocessing
- uses Gemini Flash-Lite as the default V1 model, but model choice must be configurable

Primary runtime target: MacBook Pro M1 Max, 32 GB RAM.

---

## Hard constraints — do not override without explicit PRD change

1. **Original media files stay in place.** Never copy or move originals unless an issue explicitly requests it.
2. **V1 is local-first.** GCP deployment is deferred.
3. **No face identity in V1.** No face recognition, person identity management, or biometric clustering.
4. **Only photos and videos in V1.** No special workflows for scanned documents, memes, or web images.
5. **AI-first extraction by default.** Deterministic tools (ExifTool, ffprobe, hashing, thumbnails) are essential for provenance, not optional.
6. **Model choice must be configurable.** Never hardcode Gemini or any single provider in business logic.
7. **Single-user private app.** Optimize for one trusted user on localhost; no multi-tenant patterns.

---

## Architecture

```
apps/
  api/        FastAPI — API contracts and orchestration endpoints
  web/        Next.js — gallery, inspection, review, jobs, settings
  worker/     Background jobs and ingestion/enrichment pipelines

packages/
  core/       Domain models, config, shared schemas
  db/         Migrations, repositories, SQL
  media/      ExifTool / ffprobe / thumbnails / keyframes wrappers
  models/     Model router and provider adapters
  ocr/        OCR normalization
  vision/     Extraction orchestration
  search/     Search and ranking
  storage/    Local filesystem adapter

config/       YAML config files (default.yaml, local.yaml)
prompts/      Prompt text and schema versions (outside business logic)
scripts/      Local dev and operational scripts
tests/        Test fixtures and integration tests
```

**Key boundaries:**
- `apps/` contains app-specific glue; `packages/` contains reusable logic only
- PostgreSQL is the catalog; JSONB for raw model outputs and provenance retention
- Worker owns all ingestion and enrichment jobs; API orchestrates on request

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, uv |
| Frontend | Next.js 16 App Router, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic migrations |
| AI extraction | Gemini Flash-Lite (default, swappable via config) |
| Deterministic tools | ExifTool, ffprobe |
| Worker | Local background job runner via FastAPI BackgroundTasks |
| Dev runtime | Docker Compose (PostgreSQL), uv (Python), npm (Next.js) |

---

## Coding conventions

### General
- Typed, explicit, boring code over clever abstractions.
- Small functions named by behavior.
- Pipelines must be restartable and idempotent.
- Structured logging with timestamps on all operational and debug logs.
- Machine-friendly error messages.
- Prompt text and schema versions live in `prompts/`, not in business logic.

### Python (FastAPI / worker / packages)
- Pydantic models for all request/response and extraction schemas.
- SQLAlchemy only if it materially improves maintainability; direct typed SQL is acceptable.
- Separate transport models from persistence logic.
- No hidden globals.
- External tools (ExifTool, ffprobe, model APIs) wrapped in small adapters in `packages/`.
- Every long-running operation must have job-state visibility.

### Next.js (frontend)
- Fast, minimal interface. Desktop-first, responsive.
- Server-safe data contracts and stable API hooks.
- Presentational components where possible.
- Virtualization for large grids (the archive can have hundreds of thousands of assets).
- Dark/light theme switch: simple and global.
- No decorative UI libraries unless they clearly reduce implementation cost.

### Database
- Migrations from the start; every schema change has a migration file.
- Normalized core entities; JSONB for raw model outputs.
- Never collapse curated assertions and raw model responses into one column.
- Preserve extraction history; supersede old outputs without destructive deletion.
- Indexes designed for search-heavy reads.

---

## Extraction design

### AI extraction uses the model router for:
- OCR and contextual text interpretation
- Scene classification
- Object extraction
- Place hints
- Non-identity person-region attributes (clothing, position — no biometrics)
- Video keyframe interpretation

### Deterministic tools handle:
- SHA-256 hashing and perceptual hash fingerprints
- Exact timestamps (EXIF, video, filesystem)
- Exact media/container facts (codec, resolution, duration)
- Thumbnail generation
- Video keyframe extraction

### Every extraction step must produce all five:
1. Raw provider output (JSONB in DB)
2. Normalized typed output (Pydantic schema)
3. Assertions or catalog records
4. Evidence pointers (links back to extraction run and source)
5. Review signals (confidence scores, conflict flags)

---

## Reprocessing is a first-class feature

Design all extraction work so that:
- A single asset can be rerun
- A collection or query result can be rerun
- A run can be triggered after prompt/schema/model changes
- History is preserved; old outputs are superseded, not deleted

Never build one-way pipelines that block reruns.

---

## What Copilot must not add

- Authentication systems beyond what the issue requires for a local V1
- GCP infrastructure unless an issue explicitly requests preparatory abstractions
- Face recognition or biometric code
- Heavy framework layers added "for future flexibility"
- Complex queueing infrastructure (event buses, microservices, distributed patterns)
- Any silent copying or moving of original files
- Extra product scope not present in the issue

---

## Handling ambiguity

When an issue is vague:
- prefer the simpler architecture
- prefer explicit typed schemas over loose JSON blobs
- prefer additive changes over rewrites
- preserve reprocessing ability and evidence trail
- avoid speculative abstractions that don't reduce near-term rework
- if an issue conflicts with the PRD, implement the smallest safe subset and state the conflict explicitly

---

## Definition of done

A feature is done when:
- code runs locally without errors
- tests cover the critical path
- configs are documented
- migrations are included where relevant
- logs and errors are readable
- behavior aligns with the PRD
- no scope expansion was silently introduced

---

## PR structure

1. Summary of what changed
2. Files added/modified
3. API/schema changes
4. Migration notes
5. Operational notes
6. Deferred items or explicit non-goals

If a change is partial, state clearly what remains.

---

## Implementation order

When multiple issues are open, resolve in this dependency order:

1. Repo scaffolding and config
2. Database and migrations
3. Storage discovery and indexing
4. Deterministic media enrichment
5. Model router and extraction schemas
6. Worker pipeline
7. Search API
8. Frontend gallery and inspection
9. Review queues
10. Polish, instrumentation, docs
