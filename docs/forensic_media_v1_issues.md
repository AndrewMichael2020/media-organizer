# Forensic Media Organizer V1 Issue Pack

Version: 1.0  
Date: 2026-03-13

This issue pack defines a reasonable V1 backlog for the **Forensic Media Organizer**.

V1 target:
- local-first
- originals stay in place
- comprehensive metadata extraction
- rich search/review/inspection
- no face identity
- no GCP deployment

This set is sized for an MVP/MLP rather than a giant program backlog.

---

## Epic 1. Repository foundation and local developer workflow

### Issue 1.1: Scaffold monorepo for API, web, worker, and shared packages
**Goal**  
Create the initial repository structure aligned to the PRD.

**Scope**
- create `apps/api`, `apps/web`, `apps/worker`
- create `packages/core`, `packages/db`, `packages/media`, `packages/models`, `packages/ocr`, `packages/search`, `packages/storage`, `packages/vision`
- create `config`, `prompts`, `scripts`, `docs`, `tests`
- add root README with local-first product statement
- add `.env.example`

**Acceptance criteria**
- repo structure matches PRD
- each app/package has minimal bootstrapping files
- root README explains purpose and run targets
- local install instructions exist

**Notes**
Keep bootstrapping light. Avoid overengineering workspace tooling.

### Issue 1.2: Add local configuration system with provider/model routing
**Goal**  
Make runtime behavior configurable from the start.

**Scope**
- add `config/default.yaml` and `config/local.yaml`
- support environment overrides
- define typed config loader in shared package
- include model routing fields for multimodal model and future fallback model
- include storage roots, derivative cache root, DB DSN, worker settings

**Acceptance criteria**
- apps can load config consistently
- config is validated at startup
- Gemini model name can be changed without code edits
- invalid config fails clearly

### Issue 1.3: Add local developer scripts and one-command startup
**Goal**  
Make local setup predictable.

**Scope**
- add scripts for DB startup, migrations, API start, web start, worker start
- add optional single command to run full local stack
- document macOS prerequisites

**Acceptance criteria**
- maintainer can start local stack from documented commands
- scripts are readable and not brittle
- startup failure paths are understandable

---

## Epic 2. Database, migrations, and catalog core

### Issue 2.1: Design and migrate core V1 catalog schema
**Goal**  
Create the initial PostgreSQL schema for asset registration and extraction history.

**Scope**
- create tables for `asset`, `asset_file_version`, `asset_hash`, `asset_media_info`, `asset_temporal`, `asset_location`, `asset_thumbnail`, `keyframe`, `ocr_document`, `ocr_segment`, `object_detection`, `scene_summary`, `place_candidate`, `extraction_run`, `assertion`, `assertion_evidence`, `job_run`, `review_action`, `collection`, `collection_asset`
- add migration files
- add core indexes

**Acceptance criteria**
- schema migrates cleanly on empty DB
- rollback path exists where practical
- keys and indexes support expected read paths
- raw outputs and normalized outputs are not collapsed together

### Issue 2.2: Implement repository layer for core catalog writes and reads
**Goal**  
Create clean DB access patterns for assets, runs, assertions, and review records.

**Scope**
- repository methods for insert/update/upsert patterns
- asset lookup by path, hash, and ID
- extraction run persistence
- assertion persistence with supersession support
- job status persistence

**Acceptance criteria**
- read/write paths cover V1 needs
- duplicate records are handled safely
- repository behavior is tested on main flows

### Issue 2.3: Add full-text search foundations and search-ready fields
**Goal**  
Prepare PostgreSQL for OCR and metadata search.

**Scope**
- define search-ready normalized columns or materialized structures
- add FTS indexes for OCR, scene text, place names, and summaries
- document intended ranking inputs

**Acceptance criteria**
- text search works over seeded sample records
- core search paths are indexed
- schema does not require later destructive redesign

---

## Epic 3. Local storage registration without moving originals

### Issue 3.1: Build local filesystem storage adapter and source-root registration
**Goal**  
Represent source roots and asset locations without copying originals.

**Scope**
- register one or more source roots
- resolve canonical local URIs
- normalize path handling
- record source-root identity and path history

**Acceptance criteria**
- system can point at configured directories
- asset record stores canonical path info
- path movement can be detected later

### Issue 3.2: Implement discovery scan and incremental rescan
**Goal**  
Scan directories recursively and register assets incrementally.

**Scope**
- recursive scan over configured roots
- identify supported media types: photo, video, unsupported
- first-seen / last-seen tracking
- detect new, missing, and changed files
- support resumable scan progress

**Acceptance criteria**
- first scan registers all supported assets found
- second scan only updates delta work
- unsupported files are skipped but visible in scan summary

### Issue 3.3: Compute canonical hashes and near-duplicate fingerprints
**Goal**  
Enable identity and duplicate workflows.

**Scope**
- compute SHA-256 for canonical file identity
- compute perceptual hash variants for visual similarity workflows
- persist hash outputs and timings

**Acceptance criteria**
- exact duplicates can be identified reliably
- pHash-like fingerprints are stored for later clustering
- hashing work is restartable

---

## Epic 4. Deterministic media enrichment and derivatives

### Issue 4.1: Wrap ExifTool and ffprobe as reliable adapters
**Goal**  
Capture exact metadata and media/container facts.

**Scope**
- adapter for ExifTool extraction
- adapter for ffprobe extraction
- normalized output contracts
- raw payload retention for provenance

**Acceptance criteria**
- adapters work on sample photos and videos
- raw and normalized outputs are both persisted
- tool failures produce actionable errors

### Issue 4.2: Implement temporal reconstruction and best-timestamp logic
**Goal**  
Produce one practical timeline view from competing timestamps.

**Scope**
- capture EXIF/video/filesystem/import timestamps
- implement `best_timestamp`, confidence, and source fields
- preserve all original timestamps
- record timezone source and confidence where inferable

**Acceptance criteria**
- asset inspection can show both raw and best timestamps
- conflicting timestamp cases are represented cleanly
- low-confidence temporal cases can enter review queue

### Issue 4.3: Generate thumbnails and video keyframes into derivative cache
**Goal**  
Create lightweight media derivatives without copying originals.

**Scope**
- thumbnail generation for images
- configurable keyframe extraction for videos
- derivative cache layout and retention policy
- DB linkage to derivative files

**Acceptance criteria**
- gallery can render thumbnails quickly
- video assets have representative keyframes
- derivatives are stored separately from originals

---

## Epic 5. Multimodal model router and extraction schemas

### Issue 5.1: Implement provider-agnostic multimodal model router
**Goal**  
Abstract model calls so Gemini can be swapped by config.

**Scope**
- provider interface for multimodal extraction
- Gemini implementation as default
- future-local-provider placeholder interface
- request/response tracing and cost-related metadata fields

**Acceptance criteria**
- extraction path calls provider through interface, not hardcoded vendor logic
- Gemini model name comes from config
- provider failures surface clearly

### Issue 5.2: Define strict extraction schemas and schema-versioning rules
**Goal**  
Ensure structured outputs are stable and reprocessable.

**Scope**
- Pydantic or equivalent typed schema definitions for image/video extraction
- schema version field
- prompt-to-schema contract rules
- JSON validation and recovery behavior

**Acceptance criteria**
- invalid model output is detected and logged
- valid output maps to typed schema
- schema version is persisted with extraction run

### Issue 5.3: Author V1 image extraction prompt set for comprehensive metadata
**Goal**  
Write prompts that maximize useful metadata instead of generic captioning.

**Scope**
- prompt for image extraction
- prompt for video keyframe extraction
- instructions for OCR, scene, place, people-without-identity, objects, animals, and forensic utility scoring
- output strictly in schema

**Acceptance criteria**
- prompts are stored outside code logic
- sample outputs show rich structured metadata
- prompts avoid camera-trivia emphasis unless necessary for provenance

---

## Epic 6. AI extraction pipeline and normalization

### Issue 6.1: Build image extraction pipeline from asset to typed output
**Goal**  
Run multimodal extraction for image assets and persist results.

**Scope**
- prepare image payload
- call model router
- validate structured output
- persist extraction run, raw output, normalized output, and review signals

**Acceptance criteria**
- image asset can be extracted end to end
- failed extractions are recorded without corrupting catalog state
- re-run path is possible

### Issue 6.2: Build video extraction pipeline using keyframes
**Goal**  
Support useful metadata extraction from video without full heavy processing.

**Scope**
- select keyframes from deterministic stage
- run keyframe-level extraction
- consolidate results into video-level outputs
- support transcript placeholder for later audio phase

**Acceptance criteria**
- video asset receives scene/object/place/OCR metadata from keyframes
- keyframe evidence links are persisted
- consolidation logic is documented and testable

### Issue 6.3: Normalize OCR, scene, place, object, and person-region outputs into catalog records
**Goal**  
Convert model results into durable searchable records.

**Scope**
- OCR documents and segments
- object detections
- scene summaries
- place candidates
- person-region descriptors without identity
- review priority and confidence handling

**Acceptance criteria**
- typed outputs map into catalog tables cleanly
- search-ready fields are populated
- low-confidence outputs can be filtered and reviewed

### Issue 6.4: Write structured assertions and evidence pointers
**Goal**  
Preserve why the system believes something.

**Scope**
- assertion writer
- evidence pointer model
- supersession logic
- user-verified flag plumbing for future UI actions

**Acceptance criteria**
- important facts become structured assertions
- each assertion links to extraction run and evidence
- old assertions can be superseded without silent deletion

---

## Epic 7. Job orchestration, retries, and reprocessing

### Issue 7.1: Implement local worker job framework and job state tracking
**Goal**  
Run ingestion and extraction tasks reliably on localhost.

**Scope**
- job types for scan, enrich, extract, reprocess
- job_run persistence
- retry and failure states
- lightweight concurrency controls for M1 Max memory limits

**Acceptance criteria**
- long-running work is visible as jobs
- job state survives process restarts where practical
- concurrency limits are configurable

### Issue 7.2: Add targeted reprocessing by asset, collection, and search query
**Goal**  
Make reprocessing a normal workflow.

**Scope**
- reprocess one asset
- reprocess collection
- reprocess query result set
- reprocess with changed prompt/schema/model settings

**Acceptance criteria**
- operator can rerun subsets without full re-index
- new runs do not destroy prior provenance
- API and CLI both support reruns

---

## Epic 8. API surface for assets, search, review, and jobs

### Issue 8.1: Build asset inspection and listing endpoints
**Goal**  
Expose asset records cleanly to the frontend.

**Scope**
- `GET /api/assets`
- `GET /api/assets/{id}`
- filters, sorting, and pagination
- inspection payload including raw and curated metadata sections

**Acceptance criteria**
- gallery and inspection pages can be powered from these endpoints
- payload shape is documented and typed
- slow paths are avoided on common list views

### Issue 8.2: Build search and facets API
**Goal**  
Support search across OCR, time, place, scene, object, and review signals.

**Scope**
- `POST /api/search`
- `GET /api/facets`
- text search, structured filters, and sort options
- duplicate cluster and review-state filtering

**Acceptance criteria**
- one endpoint can drive main gallery query behavior
- facets reflect current result set or documented global behavior
- search contracts are stable and typed

### Issue 8.3: Build jobs and review endpoints
**Goal**  
Let the UI start work and triage results.

**Scope**
- `POST /api/jobs/ingest`
- `POST /api/jobs/reprocess`
- `GET /api/jobs/{id}`
- review queue endpoints
- review-decision write endpoint

**Acceptance criteria**
- frontend can launch and observe core jobs
- review pages can fetch queue data
- decisions are persisted and traceable

---

## Epic 9. Next.js frontend for gallery, inspection, review, and jobs

### Issue 9.1: Create shell app, global layout, and black/white theme switch
**Goal**  
Lay down the frontend frame for the product.

**Scope**
- Next.js app shell
- primary navigation: Gallery, Asset, Places, Review, Jobs, Settings
- switchable black/white background theme
- responsive but desktop-first layout

**Acceptance criteria**
- app boots locally
- navigation skeleton is in place
- theme switch affects core surfaces consistently

### Issue 9.2: Build virtualized gallery page with fast filters and badges
**Goal**  
Make browsing large result sets practical.

**Scope**
- virtualized thumbnail grid
- search bar and filter rail
- badges for OCR, GPS, video, duplicate, scene, review flags
- selection state for batch actions later

**Acceptance criteria**
- gallery handles large result sets without obvious slowdown
- filter state is reflected in URL or equivalent persistent state
- clicking item opens inspection view

### Issue 9.3: Build asset inspection page with evidence-first layout
**Goal**  
Show one asset deeply, not as a generic photo page.

**Scope**
- main preview area
- side panels for timeline, OCR, scene, place, objects, person-region descriptors, provenance, hashes, extraction history
- evidence links to thumbnails/keyframes/raw outputs where appropriate

**Acceptance criteria**
- user can understand both “what the asset is” and “why the system thinks so”
- raw and curated metadata are visually distinct
- page is usable for both photos and videos

### Issue 9.4: Build review pages for duplicates, OCR-rich items, and metadata conflicts
**Goal**  
Support human triage of high-value queues.

**Scope**
- duplicate review page
- OCR-rich review page
- timestamp/place conflict review page
- persist review decisions

**Acceptance criteria**
- review pages are fed from queue endpoints
- user can mark items as reviewed or defer them
- review actions are stored in catalog

### Issue 9.5: Build jobs page and settings page
**Goal**  
Expose operational visibility and runtime config context.

**Scope**
- jobs list and detail view
- settings summary page showing source roots, derivative cache, model config, and batch parameters
- no secret values shown

**Acceptance criteria**
- operator can see what the system is doing
- settings page reflects effective configuration
- no sensitive values leak into UI

---

## Epic 10. Review queues and duplicate handling

### Issue 10.1: Implement duplicate and near-duplicate clustering logic
**Goal**  
Turn hashes and similarity signals into reviewable clusters.

**Scope**
- exact duplicate grouping
- near-duplicate candidate grouping
- cluster summaries for UI
- configurable thresholds

**Acceptance criteria**
- duplicates view shows meaningful groups
- exact and near-duplicate cases are distinguished
- thresholds can be tuned without code rewrite

### Issue 10.2: Implement review-priority scoring and queue materialization
**Goal**  
Surface what matters first.

**Scope**
- compute review priority from confidence, OCR richness, temporal conflicts, extraction failures, and duplicate signals
- materialize or query queue views

**Acceptance criteria**
- review page ordering is explainable
- priority logic is documented
- queue generation is testable

---

## Epic 11. CLI workflows and operations

### Issue 11.1: Add CLI commands for scan, enrich, extract, search, and reprocess
**Goal**  
Allow backend use without the frontend.

**Scope**
- CLI for scanning roots
- CLI for running deterministic enrichment
- CLI for extraction
- CLI for targeted reprocess
- CLI for simple search/export diagnostics

**Acceptance criteria**
- critical workflows can run without web UI
- commands are documented and predictable
- output is useful for debugging

### Issue 11.2: Add operational logging and run summaries
**Goal**  
Make batch behavior observable.

**Scope**
- structured logs with timestamps
- per-job summary stats
- extraction error categories
- model/provider usage summaries

**Acceptance criteria**
- logs are readable during long runs
- failures can be triaged from logs and DB state
- summaries do not require spelunking raw files only

---

## Epic 12. Testing and seed data

### Issue 12.1: Create V1 seed dataset and fixture strategy
**Goal**  
Enable local repeatable testing without relying on the full personal archive.

**Scope**
- small curated fixture set of photos and short videos
- expected metadata snapshots where practical
- fixture documentation

**Acceptance criteria**
- developers can run tests against a small dataset
- fixtures cover OCR, GPS, indoor/outdoor, duplicate, and video cases

### Issue 12.2: Add tests for catalog, adapters, extraction normalization, and search
**Goal**  
Cover the most failure-prone paths.

**Scope**
- DB/repository tests
- ExifTool and ffprobe adapter tests where possible
- schema validation tests
- normalization tests
- search API tests

**Acceptance criteria**
- critical pipelines have automated coverage
- tests can run locally without special infra beyond documented prerequisites

---

## Epic 13. Documentation for maintainability

### Issue 13.1: Write implementation README for local runtime and operator workflow
**Goal**  
Document how to run and reason about the system.

**Scope**
- startup instructions
- scan/extract/reprocess workflow
- model config explanation
- derivative cache explanation
- database migration workflow
- troubleshooting section

**Acceptance criteria**
- new contributor or future self can run the project from docs
- docs match actual commands and config

### Issue 13.2: Write schema and extraction-contract documentation
**Goal**  
Reduce future drift between prompts, DB, and API.

**Scope**
- document extraction schema versions
- document assertion model
- document review queues
- document API contracts at a practical level

**Acceptance criteria**
- schema docs align with code
- extraction contract evolution path is explained

---

## Suggested execution order

Recommended order for implementation:

1. Issue 1.1
2. Issue 1.2
3. Issue 2.1
4. Issue 3.1
5. Issue 3.2
6. Issue 4.1
7. Issue 4.2
8. Issue 4.3
9. Issue 5.1
10. Issue 5.2
11. Issue 5.3
12. Issue 6.1
13. Issue 6.2
14. Issue 6.3
15. Issue 6.4
16. Issue 7.1
17. Issue 8.1
18. Issue 8.2
19. Issue 9.1
20. Issue 9.2
21. Issue 9.3
22. Issue 10.1
23. Issue 10.2
24. Issue 8.3
25. Issue 9.4
26. Issue 9.5
27. Issue 11.1
28. Issue 11.2
29. Issue 12.1
30. Issue 12.2
31. Issue 13.1
32. Issue 13.2
33. Issue 1.3
34. Issue 2.2
35. Issue 2.3
36. Issue 7.2

## Minimal launch definition for V1

V1 is ready when all of the following are true:
- local scan registers photo and video assets without moving originals
- deterministic metadata and derivatives are generated
- Gemini-driven extraction produces structured metadata for images and videos
- OCR, scene, place, object, and person-region descriptors are searchable
- gallery and inspection UI are usable locally
- duplicate and review queues exist
- reprocessing is supported
- core docs and tests exist

## Explicitly deferred after V1

These should be separate future issue packs:
- face detection and face identity pipeline
- local VLM fallback providers such as Qwen-VL-class models
- GCP storage/Cloud Run/Cloud SQL architecture
- stronger auth beyond local private runtime
- mobile workflows
