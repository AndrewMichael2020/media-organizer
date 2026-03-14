# GitHub Copilot Instructions for Forensic Media Organizer

Version: 1.0  
Date: 2026-03-13

This document guides GitHub CLI Copilot and coding agents working on the **Forensic Media Organizer** repository.

## 1. Product intent

Build a **local-first, single-user forensic media organizer** for a private archive of photos and videos.

The product is not a generic consumer gallery. It is a metadata-and-evidence system that:
- leaves originals in place
- extracts rich structured metadata
- stores derived artifacts separately
- supports fast search, inspection, review, and reprocessing
- uses configurable multimodal extraction, with Gemini Flash-Lite as the default V1 model

## 2. Hard constraints

These are locked unless a maintainer explicitly changes the PRD.

1. **Original media files stay in place by default.** Do not design features that copy or relocate the archive unless the issue explicitly requests it.
2. **V1 is local-first.** GCP deployment is deferred.
3. **V1 excludes face identity.** Do not add face recognition, person identity management, or biometric clustering unless the issue explicitly opens that scope.
4. **Only photos and videos are in scope for V1.** Do not build special workflows for scanned documents, downloaded web images, memes, or composite-image pipelines.
5. **AI-first extraction is the default.** Deterministic tools still matter for provenance, timestamps, hashing, thumbnails, video facts, and exact media/container metadata.
6. **Model choice must be configurable.** Do not hardcode Gemini or any single provider in business logic.
7. **Single-user private app.** Optimize for one trusted user on localhost, not for multi-tenant patterns.

## 3. How to interpret vague requests

When an issue is ambiguous:
- prefer the simpler architecture
- prefer explicit typed schemas over loosely shaped JSON blobs
- prefer additive changes over broad rewrites
- preserve reprocessing ability
- preserve evidence and provenance
- avoid speculative abstractions unless they directly reduce future rework

Do not invent extra product scope.

## 4. Architecture expectations

Repository shape:

```text
apps/
  api/        FastAPI app
  web/        Next.js app
  worker/     background jobs and pipelines
packages/
  core/       domain models, config, shared schemas
  db/         migrations, repositories, SQL
  media/      exiftool/ffprobe/thumbnails/keyframes wrappers
  models/     model router and provider adapters
  ocr/        OCR normalization
  vision/     extraction orchestration
  search/     search and ranking
  storage/    local filesystem adapter
```

Expectations:
- FastAPI owns API contracts and orchestration endpoints
- Next.js owns gallery, inspection, review, jobs, settings
- PostgreSQL is the catalog
- worker owns ingestion and enrichment jobs
- packages contain reusable logic, not app-specific glue

## 5. Coding style and implementation rules

### General
- Prefer clear, typed, boring code over clever code.
- Keep functions small and name them by behavior.
- Make pipelines restartable and idempotent where possible.
- Use structured logging.
- Include timestamps in debug and operational logs.
- Return machine-friendly error messages.
- Keep prompt text and schema versions outside business logic where practical.

### Python backend
- Use Pydantic models for request/response and extraction schemas.
- Use SQLAlchemy only if it materially improves maintainability; otherwise a direct SQL approach is acceptable if kept clean and typed.
- Separate transport models from persistence logic.
- Avoid hidden globals.
- Wrap external tools with small adapters.
- Ensure every long-running operation has job-state visibility.

### Next.js frontend
- Build a fast, minimal interface.
- Prefer server-safe data contracts and stable API hooks.
- Keep components presentational where possible.
- Use virtualization for large grids.
- Keep dark/light switch simple and global.
- Do not add decorative UI libraries unless they clearly reduce implementation cost.

### Database
- Use migrations from the start.
- Normalize core entities, but allow JSONB for raw model outputs and provenance retention.
- Preserve extraction history.
- Do not collapse curated assertions and raw responses into one column.
- Design indexes for search-heavy reads.

## 6. Metadata philosophy for V1

V1 is intentionally comprehensive on useful metadata.

Good metadata:
- improves search or filtering
- improves review prioritization
- preserves provenance
- supports later reprocessing or better models
- captures evidence for why the system believes something

Avoid foregrounding low-value camera trivia such as ISO or aperture in the product UX unless an issue explicitly asks for it. Such fields may remain in raw metadata storage if cheaply available.

## 7. Extraction design rules

### AI-first extraction
Use the configured multimodal model for:
- OCR plus contextual interpretation
- scene classification
- object extraction
- place hints
- non-identity person-region attributes
- video keyframe interpretation

### Deterministic support
Use deterministic tooling for:
- hashing
- exact timestamps
- exact media/container facts
- thumbnail generation
- video keyframes
- provenance retention

### Output contracts
Every extraction step should aim to produce:
1. raw provider output
2. normalized typed output
3. assertions or catalog records
4. evidence pointers
5. review signals

## 8. Reprocessing rules

Reprocessing is a first-class feature.

Any extraction work should be designed so we can:
- rerun one asset
- rerun a collection or query result
- rerun after prompt/schema/model changes
- preserve history
- supersede old outputs without destructive loss

Do not implement one-way pipelines that prevent reruns.

## 9. What Copilot should avoid

Do not:
- add authentication systems beyond what the issue requires for local V1
- add GCP infrastructure to V1 code unless the issue explicitly requests preparatory abstractions
- add face recognition code in V1
- add massive framework layers “for future flexibility”
- add queueing infrastructure more complex than needed for a local worker
- add event buses, microservices, or distributed patterns for a localhost MVP
- silently change file-storage assumptions
- silently add copying of originals

## 10. How to structure deliverables in pull requests

When implementing an issue, prefer this structure:

1. Summary of what changed
2. Files added/modified
3. API/schema changes
4. Migration notes
5. Operational notes
6. Deferred items or explicit non-goals

If a change is partial, state clearly what remains.

## 11. Preferred issue execution order

When several issues are open, prefer this dependency order:
1. repo scaffolding and config
2. database and migrations
3. storage discovery/indexing
4. deterministic media enrichment
5. model router and extraction schemas
6. worker pipeline
7. search API
8. frontend gallery and inspection
9. review queues
10. polish, instrumentation, docs

## 12. Definition of done

A feature is done when:
- code compiles and runs locally
- tests cover the critical path at the right level
- configs are documented
- migrations are included where relevant
- logs and errors are readable
- behavior aligns with the PRD
- no hidden scope expansion was introduced

## 13. Escalation rule

If an issue conflicts with the PRD, do not guess. Implement the smallest safe subset and state the conflict clearly in the output.
