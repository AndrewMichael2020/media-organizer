# Forensic Media Organizer
## Product Requirements Document (PRD) and System Blueprint

Version: 1.0  
Date: 2026-03-13  
Authoring context: local-first personal software product for a single private user  
Primary target runtime: MacBook Pro M1 Max, 32 GB RAM  
Secondary future target: Google Cloud Platform deployment after Version 1  

---

## 1. Executive summary

This product is a **private forensic-grade media organizer** for a very large personal archive of photos and videos.

It is being built because standard photo libraries and gallery apps are weak at four things that matter here:

1. They are optimized for casual viewing rather than deep inspection.
2. They do not extract enough structured knowledge from images and videos.
3. They do not preserve a strong evidence trail showing how a conclusion was produced.
4. They do not support serious reprocessing as models improve.

The product should let one user ingest tens or hundreds of thousands of local media assets, leave originals in place, build a rich metadata and inference layer around them, and then search, filter, inspect, cluster, and review that archive with far more precision than a normal consumer photo tool.

This is **not** a client-facing platform, not a social gallery, not a family photo-sharing app, and not an enterprise DAM product. It is a **single-user private analytical system** that treats a personal media archive as a searchable body of evidence and memory.

Version 1 should focus on **comprehensive metadata extraction and review**, not on face identity and not on cloud deployment.

---

## 2. Product vision

### 2.1 One-sentence vision

Build a private local-first application that can look at a large personal media archive and turn it into a structured, searchable, evidence-backed knowledge system.

### 2.2 Long-form vision

The user is a photographer and collector of large volumes of visual material. The archive includes iPhone photos, Nikon photos, videos, screenshots, and other image assets accumulated over many years. The problem is not only storage or casual browsing. The problem is **retrieval, interpretation, categorization, and reconstruction**.

The user wants to answer questions such as:

- Show me every asset that likely took place in a hospital room.
- Show me images with snow, skis, and at least two people.
- Show me bar or restaurant interiors at night with readable signs.
- Show me images taken during the same likely event even when timestamps are weak.
- Show me all assets containing a visible iPhone in someone’s hand.
- Show me photos with animals and extract species, gear, and context.
- Show me all text seen in the archive and where it appeared.
- Show me repeated places, repeated bags, repeated clothing, repeated settings.

The product therefore needs to do much more than generate captions. It needs to create a **durable metadata system** with provenance, confidence, evidence, and reprocessability.

---

## 3. Product purpose and business case

### 3.1 Why this product exists

The business case is not revenue. The business case is **personal analytical value per hour saved** and **increased retrieval power over a growing archive**.

Without this product, the user has a growing archive of visual material that becomes harder to use every year. Even if the files remain safe, they become progressively less useful because the user cannot reliably find, group, compare, and interpret them. Traditional folders and gallery tools do not solve this once the archive becomes very large and semantically complex.

### 3.2 Core value proposition

This product creates value in six ways:

#### A. Retrieval value
The user can find relevant assets by meaning, not only by filename or date.

#### B. Forensic value
The user can inspect how each conclusion was produced, with evidence and confidence rather than opaque magic.

#### C. Curation value
The user can progressively refine the archive, review weak results, and improve structured knowledge over time.

#### D. Reprocessing value
The system can be rerun when models improve, without rethinking the entire repository or moving originals.

#### E. Preservation value
Original media stays in place, which reduces storage duplication and operational churn.

#### F. Extensibility value
The local-first metadata architecture can later be extended to cloud deployment without redesigning the whole product.

### 3.3 Why local-first is the correct economic and technical choice

Local-first is correct for Version 1 because:

- the archive is already local,
- moving originals creates storage duplication and operational friction,
- the user wants privacy and control,
- the main cost driver in V1 is metadata extraction, not distributed serving,
- iteration speed is higher locally,
- GCP is a future deployment concern, not a present requirement.

### 3.4 What success looks like in practical terms

A successful Version 1 would let the user point the app at large local media roots, run indexing and extraction incrementally, and then interact with a fast private UI where assets can be searched and filtered by:

- time
- place
- device family
- scene type
- activity
- OCR text
- objects
- animals
- human-presence descriptors
- duplicates and near-duplicates
- review status
- confidence

and then inspected with a clear evidence panel showing how the metadata was derived.

---

## 4. Problem statement

The user has a large personal media archive, likely six figures of assets over time, spread across local folders and devices. The archive includes highly heterogeneous content. The user does not merely want storage. The user wants structured understanding.

Existing tools fail because they usually have one or more of these weaknesses:

- weak metadata extraction,
- shallow OCR,
- weak evidence model,
- poor reprocessing support,
- weak search over inferred concepts,
- poor handling of archives that remain in place,
- consumer-gallery assumptions instead of analytical assumptions.

The result is that the archive contains significant latent value but poor practical usability.

This product exists to convert that archive into a **high-precision local media intelligence system**.

---

## 5. Product scope at a glance

### 5.1 In scope for Version 1

Version 1 should deliver a serious, usable first product that already feels powerful.

It includes:

- local-first indexing of photos and videos
- originals left in place
- deterministic file and media registration
- rich AI-first metadata extraction
- OCR extraction and search
- object, scene, activity, and setting extraction
- temporal and location reconstruction
- duplicate and near-duplicate support
- review queues and manual correction workflows
- responsive gallery and asset inspection UI
- API + CLI + worker design in one repository
- model routing via config
- storage of raw outputs and curated outputs separately
- reprocessing support as a first-class workflow

### 5.2 Explicitly out of scope for Version 1

The following should be deferred and tracked as future issue streams:

- face identity and named-person recognition
- cloud deployment on GCP
- multi-user support
- sharing or public publishing
- mobile app
- advanced relation graph UI
- fine-grained video tracking across all frames
- scanned-document specialty workflows
- downloaded-web-image specialty workflows
- meme/composite/editorial workflows

### 5.3 Important boundary decision

Version 1 should still detect that humans are present and extract visible human descriptors where feasible, but it should **not attempt identity persistence**. Identity is a later subsystem.

---

## 6. Primary user

### 6.1 User profile

There is exactly one intended user in Version 1.

That user:

- has a large private media archive,
- cares about precision and evidence,
- is comfortable running local software,
- wants a modern UI rather than pure CLI,
- wants the option to use CLI for batch workflows,
- cares about privacy and control,
- expects software-engineering quality rather than a toy script.

### 6.2 User goals

The user wants to:

- ingest media without relocating originals,
- extract as much useful structured metadata as possible,
- search by semantic meaning,
- inspect results with confidence and provenance,
- fix or verify weak metadata,
- rerun extraction later with better models,
- keep the system extensible to future cloud deployment.

### 6.3 User frustrations this product should remove

- scrolling through endless folders or albums,
- weak caption-style AI that loses detail,
- inability to search by nuanced scene or object characteristics,
- losing trust because there is no evidence trail,
- expensive or rigid cloud-first tools,
- duplicate storage and unnecessary copying of originals.

---

## 7. Product principles

These principles should govern all design and implementation decisions.

### 7.1 Originals remain in place

The product catalogs originals where they already live. It should not assume ownership of original storage in V1.

### 7.2 Metadata is the product

The core value of the system is the metadata, evidence, and retrieval layer. The media files are inputs. The product is the intelligence built around them.

### 7.3 AI-first where interpretation is needed

Use Gemini 3.1 Flash-Lite by default for economical multimodal extraction that benefits from visual interpretation and structured output.

### 7.4 Deterministic where exactness matters

Use deterministic tools for facts that should be exact and reproducible, such as file hashes, media container facts, and exact metadata reads.

### 7.5 Reprocessing is normal

The system must assume that extraction will be rerun as prompts, models, or schemas improve.

### 7.6 Evidence over hand-waving

Every meaningful inferred field should be traceable to a source run, confidence, and ideally evidence crop or source text when possible.

### 7.7 UI must be fast

The archive is large. The frontend should privilege responsiveness, virtualized browsing, and sharp inspection views.

### 7.8 Single-user private by design

No public browsing, no accidental exposure, no weak guest-facing assumptions.

---

## 8. Version 1 product goals

### 8.1 Primary goals

1. Create a working private application that can register large local media roots without moving originals.
2. Build a metadata pipeline that extracts rich useful fields from photos and videos.
3. Deliver search and inspection UX strong enough to make the archive materially more usable.
4. Support review and correction of weak or uncertain outputs.
5. Keep architecture clean enough for later issue-driven expansion.

### 8.2 Secondary goals

1. Make model choice configurable.
2. Keep deterministic and AI extraction separated but composable.
3. Preserve raw model output and normalized metadata separately.
4. Make incremental rescans and reprocessing safe and routine.

### 8.3 Non-goals for Version 1

1. Do not optimize for social presentation.
2. Do not optimize for public scalability.
3. Do not build a full knowledge graph user experience yet.
4. Do not tackle cloud architecture beyond keeping interfaces portable.

---

## 9. High-level user stories

### 9.1 Archive registration

As the user, I want to register local media roots and scan them recursively so that the system knows what exists without copying originals.

### 9.2 Search by meaning

As the user, I want to search by concepts such as place, activity, object, OCR text, or time so that I can find assets that folder names never captured.

### 9.3 Inspect one asset deeply

As the user, I want an inspection screen that shows the asset, extracted metadata, confidence, and evidence so that I can trust or challenge the system’s conclusions.

### 9.4 Review uncertain outputs

As the user, I want a review queue for uncertain or incomplete results so that I can correct important metadata instead of browsing everything manually.

### 9.5 Reprocess later

As the user, I want to rerun parts of the pipeline when prompts or models improve so that the archive becomes smarter over time.

### 9.6 Work with both UI and CLI

As the user, I want both a web UI and CLI entry points so that I can do operational work efficiently.

---

## 10. Detailed functional requirements

## 10.1 Asset registration and ingest

The system shall:

- accept one or more configured local roots,
- recursively discover supported media files,
- identify assets as image, video, or unsupported,
- register current path and source root,
- compute stable canonical asset identity,
- detect moved files where possible,
- detect changed files,
- support incremental rescans,
- support explicit ingest jobs and rescan jobs,
- record first-seen and last-seen timestamps,
- preserve path history when files move.

## 10.2 Media type handling

Version 1 shall support at minimum:

- photos
- videos
- screenshots when encountered
- unsupported files as tracked but not processed deeply

Version 1 should not build specialty workflows for scanned documents, downloaded web images, or meme/composite classes.

## 10.3 Derivatives

The system shall generate and store derivatives separately from originals, including:

- thumbnails
- optimized preview images when needed
- keyframes for video
- OCR artifacts
- evidence crops where useful

## 10.4 Extraction workflow

The system shall support a multi-stage pipeline with separate steps for:

- deterministic file/media registration
- AI metadata extraction
- OCR normalization
- duplicate analysis
- review-state assignment
- reprocessing

## 10.5 Search

The system shall support search over:

- filenames and paths
- timestamps and date ranges
- OCR text
- place and location candidates
- device family
- scene and setting labels
- objects
- animals
- human-presence descriptors
- review status
- duplicate clusters
- confidence ranges
- custom tags and collections

## 10.6 Review workflows

The system shall support review queues for:

- low-confidence extraction
- missing OCR where OCR was expected
- duplicate clusters needing merge/split decisions
- assets missing best timestamp
- place inference conflicts
- extraction failures
- assets not yet processed by a selected pipeline version

## 10.7 Reprocessing

The system shall allow:

- rerun by asset
- rerun by collection
- rerun by pipeline stage
- rerun by model version
- rerun by prompt version
- rerun by time range

Reprocessing shall not destroy historical run lineage.

---

## 11. Comprehensive metadata blueprint for Version 1

This section is the heart of the product. The system should aim to extract and normalize a broad, useful metadata layer. The goal is not to collect every possible technical fact. The goal is to collect facts that materially improve organization, retrieval, and analysis.

### 11.1 Metadata design principles

Each metadata field should be classified as one of:

- deterministic fact
- inferred fact
- heuristic flag
- review state
- lineage/provenance fact

Each inferred field should, where practical, carry:

- source extractor
- extractor version
- confidence
- evidence reference
- timestamp of extraction

### 11.2 Metadata domains

#### A. Asset identity and provenance

Purpose: uniquely identify the asset and preserve its operational history.

Fields include:

- internal asset UUID
- current canonical URI or path
- source root identifier
- relative path within root
- filename
- extension
- MIME type
- file size in bytes
- SHA-256 hash
- perceptual hash family
- ingestion batch ID
- first seen timestamp
- last seen timestamp
- last indexed timestamp
- current presence state
- path history
- host/machine profile that performed ingest
- raw metadata blob references

Why it matters:
This domain makes the archive trackable, deduplicable, and reproducible.

#### B. Temporal reconstruction

Purpose: reconstruct when the asset was likely created or captured, not only what timestamps happen to exist.

Fields include:

- EXIF original timestamp
- EXIF digitized timestamp
- video creation timestamp
- filesystem creation timestamp
- filesystem modification timestamp
- import timestamp
- best timestamp
- best timestamp source
- timestamp confidence
- timezone value when known
- timezone source
- same-session cluster ID
- probable event window ID
- chronological consistency flags

Why it matters:
Large archives often have multiple timestamps of uneven quality. The product should choose the best operational timestamp and explain why.

#### C. Acquisition and source context

Purpose: understand how the asset was produced and what kind of media it is.

Fields include:

- device family, such as iPhone 14 Pro Max or Nikon D600
- camera/software metadata when useful
- orientation
- pixel dimensions
- color profile if useful
- video duration
- frame rate
- codec
- container
- audio presence flag for video
- probable source route such as direct camera capture, edited export, sync artifact, screen capture
- screenshot probability flag
- motion-photo or live-photo related hints when available

Why it matters:
These fields help the system understand what type of asset it is dealing with and how it should be processed.

#### D. Spatial and location metadata

Purpose: reconstruct where the asset was likely taken or what place it depicts.

Fields include:

- raw GPS coordinates when present
- GPS precision if available
- normalized location cell or geohash
- place candidate name
- place type
- place confidence
- place evidence source
- repeated-location cluster
- indoor/outdoor
- environmental context such as snow, urban street, hospital corridor, airport, restaurant interior, mountain trail
- region/city candidate when inferable

Why it matters:
Location is one of the strongest retrieval dimensions in a personal archive.

#### E. Scene and setting interpretation

Purpose: describe what kind of environment and situation the asset likely shows.

Fields include:

- scene label
- setting label
- activity label
- event-likeness score
- event type candidate
- day/night/twilight estimate
- weather or environmental conditions if visually evident
- formality level if inferable
- crowd density level
- visual complexity level
- emotional tone of the overall scene when useful
- notable contextual cues

Examples:

- hospital ICU room
- bar interior at night
- ski slope in daylight
- home kitchen
- airport gate seating area
- street protest
- trailhead parking area

Why it matters:
These fields enable semantic retrieval that ordinary metadata never captures.

#### F. Human-presence descriptors without identity

Purpose: capture useful information about visible people without implementing named identity in Version 1.

Fields include, per detected human region where feasible:

- human present flag
- person region bounding box
- face visible flag
- face quality flag
- body visibility level
- approximate age band
- apparent gender presentation if the extractor provides it and if you decide to retain it
- hair color
- hair style
- facial hair
- eye visibility
- eye color when visible
- glasses or sunglasses
- headwear description
- glove description
- upper-body clothing items
- lower-body clothing items
- clothing colors per item
- outerwear descriptors
- logos or brands visible
- bags or carried items
- device visible in hand
- posture or pose
- action descriptor
- expression or forensic emotion tag
- interaction cues with nearby people or objects
- group context notes
- occlusion notes

Why it matters:
Even without identity, these features support powerful search and later issue-driven expansion.

#### G. Animal descriptors

Purpose: make animals searchable and analytically useful.

Fields include:

- animal present flag
- species
- breed candidate
- fur color or pattern
- size class
- collar/harness/leash/accessories
- activity state
- interaction context with humans or environment

Why it matters:
Animals often matter in personal archives and should be first-class searchable entities.

#### H. Objects and material culture

Purpose: identify salient objects that support search and context reconstruction.

Fields include:

- vehicles
- luggage and bags
- sports gear
- tools
- medical equipment
- phones, tablets, laptops, cameras
- furniture
- signs
- printed materials
- repeated-object hints across assets
- object prominence score
- object count when meaningful
- object spatial hints

Why it matters:
Objects often anchor memory and context more reliably than captions.

#### I. Text and language layer

Purpose: extract all visible text and make it meaningfully searchable.

Fields include:

- full OCR text
- OCR segments
- OCR bounding boxes
- language detection
- text type, such as sign, menu, screen UI, receipt, badge, label, billboard, packaging
- context explanation of the text in the scene
- normalized OCR field for search
- OCR quality score

Why it matters:
Text is one of the strongest retrieval channels in image archives.

#### J. Video enrichment

Purpose: make videos searchable beyond filename and duration.

Fields include:

- video duration and codec facts
- keyframe set
- keyframe timestamps
- transcript when audio is processed
- scene continuity hints
- best representative frame
- object continuity hints across sampled frames
- OCR over keyframes
- per-video summary assembled from keyframe metadata

Why it matters:
Videos become usable only when they gain searchable derived structure.

#### K. Duplicate and similarity intelligence

Purpose: group assets that are identical, near-identical, or semantically similar.

Fields include:

- exact duplicate cluster ID
- near-duplicate cluster ID
- similarity score
- preferred representative asset flag
- duplicate review state
- similarity explanation hints

Why it matters:
Large archives become manageable only when redundancy is visible.

#### L. Quality and processing diagnostics

Purpose: indicate whether an asset was hard to analyze or needs attention.

Fields include:

- blur or low-detail suspicion
- overexposure/underexposure suspicion when useful
- obstruction or occlusion flags
- low OCR quality flag
- extraction failure flags
- stage completion flags
- last successful pipeline stage
- needs review flag
- review reason

Why it matters:
This enables targeted review rather than blind manual checking.

#### M. Curation and user-applied metadata

Purpose: allow the user to refine the archive over time.

Fields include:

- custom tags
- collections
- star/bookmark status
- manual notes
- manual correction records
- manual place overrides
- review decisions
- hide/archive state within the product

Why it matters:
The system becomes more useful when machine output and human curation coexist cleanly.

#### N. Extraction lineage and evidence

Purpose: preserve trust.

Fields include:

- extractor name
- model name
- model version
- prompt version
- extraction timestamp
- raw output reference
- normalized output reference
- confidence
- evidence crop reference when applicable
- normalization rules applied
- superseded-by / supersedes relations for reruns

Why it matters:
This is what separates a trustworthy analytical system from a black-box toy.

---

## 12. Architecture overview

Version 1 should be designed as one repository with three operational surfaces:

1. **Backend API** for the web app
2. **CLI** for direct operational tasks
3. **Workers** for extraction and batch processing

All three surfaces should use the same underlying application services rather than duplicating logic.

### 12.1 Logical architecture

- **Frontend**: React + Next.js
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Originals**: remain in place on local storage
- **Derivatives**: generated and stored in a dedicated local app-managed area
- **Workers**: local asynchronous job workers
- **Model adapters**: configurable extraction providers

### 12.2 Design stance on storage

The system should behave like a metadata overlay on top of a local archive.

It should store:

- references to originals,
- extracted metadata,
- derivatives,
- run history,
- review state,
- user curation.

It should not duplicate originals by default.

---

## 13. Recommended repository structure

```text
forensic-media-organizer/
  apps/
    web/                     # Next.js frontend
    api/                     # FastAPI backend
    worker/                  # local job runner / task entrypoints
    cli/                     # CLI wrapper or Typer app
  packages/
    core/                    # domain models, shared types, business rules
    config/                  # config loading and validation
    extractors/
      gemini/                # Gemini adapters and prompts
      deterministic/         # exiftool, ffprobe, hashes, OCR wrappers
      local_vlm/             # future local VLM adapters, not required in V1
    pipelines/               # orchestrated extraction stages
    persistence/             # DB access and repository layer
    search/                  # search query composition
    review/                  # review queues and actions
    media/                   # thumbnail/keyframe/evidence generation
  infra/
    local/                   # docker compose, local scripts, env examples
    future-gcp/              # placeholder only, no V1 implementation required
  docs/
    prd/
    architecture/
    prompts/
    issues/
  data/
    derivatives/             # local generated derivatives
    logs/
  tests/
    unit/
    integration/
    fixtures/
```

This structure keeps product logic separate from app shells and makes later deployment changes easier.

---

## 14. Backend service design

### 14.1 Core backend responsibilities

The backend should:

- expose asset and search APIs,
- manage ingest and extraction jobs,
- surface review queues,
- return normalized metadata and raw lineage references,
- support manual corrections,
- coordinate reprocessing.

### 14.2 CLI responsibilities

The CLI should support commands such as:

- register roots
- scan
- ingest
- extract metadata
- extract OCR
- build thumbnails
- detect duplicates
- reprocess
- export metadata
- run diagnostics

### 14.3 Worker responsibilities

Workers should execute queued jobs, such as:

- initial extraction
- retry extraction
- thumbnail generation
- video keyframe generation
- OCR normalization
- duplicate analysis
- review materialization

---

## 15. Model strategy for Version 1

### 15.1 Default model direction

Use **Gemini 3.1 Flash-Lite** as the default multimodal metadata extractor because it is cost-oriented and suitable for large-volume extraction tasks.

### 15.2 Why Gemini should not be the only extraction mechanism

Gemini is appropriate for:

- visual scene interpretation
- object/setting/activity extraction
- rich structured outputs
- text-in-context interpretation
- image-to-JSON extraction

Gemini should not replace deterministic tools for:

- exact file hashes
- exact media container facts
- exact metadata reads
- operational provenance

### 15.3 Configuration requirement

Model choice must be externalized in config so that the system can later switch to:

- a stronger Gemini model,
- a local VLM,
- a hybrid route,
- staged extraction policies.

### 15.4 Face pipeline decision

Version 1 should not implement face identity. That work should be deferred.

Version 1 may keep a placeholder contract for future human-region or face-region metadata if that helps future expansion, but implementation is optional.

---

## 16. Deterministic extraction strategy

Although the product is AI-first for interpretation, deterministic extraction is still necessary.

### 16.1 Deterministic tools in V1

Use deterministic tooling for:

- file hashing
- MIME/type detection
- EXIF and embedded metadata reads
- video/container/codec facts
- key operational timestamps
- OCR fallback or structured OCR stage if needed

### 16.2 Why deterministic is still necessary

The product must know the difference between:

- a model opinion,
- a file fact,
- a metadata fact,
- a heuristic,
- a user-confirmed correction.

Without that separation, trust will erode and reprocessing will become confusing.

---

## 17. Search and retrieval design

The search experience should be one of the main reasons the product exists.

### 17.1 Search modes

The frontend should support at least these modes:

- simple keyword search
- structured filters
- saved searches
- review queues as saved operational views

### 17.2 Filter dimensions

Filters should include:

- date and time range
- place or location
- device family
- media type
- scene type
- activity
- objects
- animals
- OCR text presence
- review state
- duplicate state
- confidence threshold
- extraction version

### 17.3 Future-friendly search stance

Even if Version 1 uses standard PostgreSQL querying and JSONB, the domain model should not block future vector search or graph-like exploration.

---

## 18. Frontend and UX requirements

### 18.1 UX philosophy

The frontend should feel like an artful private gallery combined with an analytical inspection console.

It should be:

- minimalist,
- dark/light switchable,
- responsive,
- keyboard-friendly,
- visually clean,
- dense where inspection requires density.

### 18.2 Primary screens

Version 1 should include at least:

1. Authentication gate for one private user
2. Main gallery
3. Search/filter panel
4. Asset inspection page
5. Review queues page
6. Job status page
7. Settings/config view

### 18.3 Gallery requirements

The gallery should:

- support virtualized infinite scrolling,
- show thumbnails fast,
- surface badges for important metadata,
- support multi-select,
- support quick filtering,
- support switching background between light and dark.

### 18.4 Inspection page requirements

The inspection page should show:

- large asset preview
- key metadata summary
- OCR panel
- scene/object/setting panel
- timestamps and provenance panel
- extraction lineage
- review actions
- reprocess actions

### 18.5 Review experience

The review UI should let the user:

- confirm or reject weak metadata,
- correct place or time,
- flag extraction failures,
- mark duplicate decisions,
- add tags or notes.

---

## 19. ASCII wireframes

### 19.1 Main gallery

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ FORENSIC MEDIA ORGANIZER                                              ◐ Light / Dark      │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Search [ person-free V1 / place / object / OCR / activity / date / device ] [ Run ]       │
│ Filters: [Photos] [Videos] [OCR] [Animals] [Objects] [Night] [Hospital] [Snow] [Review]   │
│          [Date Range ▼] [Device ▼] [Place ▼] [Duplicate ▼] [Confidence ▼]                 │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Collections / Views                Main gallery                                             │
│ ┌──────────────────────────────┐   ┌─────────────────────────────────────────────────────┐ │
│ │ All assets                   │   │  □□□ □□□ □□□ □□□ □□□ □□□ □□□ □□□                 │ │
│ │ New ingest                   │   │  □□□ □□□ □□□ □□□ □□□ □□□ □□□ □□□                 │ │
│ │ Needs review                 │   │  each card shows thumbnail + key badges            │ │
│ │ OCR rich                     │   │  [ocr] [video] [gps] [night] [hospital?]          │ │
│ │ Near duplicates              │   │  [snow] [animal] [needs-review]                   │ │
│ │ Place clusters               │   │                                                     │ │
│ │ Time gaps                    │   │                                                     │ │
│ └──────────────────────────────┘   └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ Bottom action bar: [Compare] [Tag] [Queue Reprocess] [Export Metadata] [Open Review]       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Asset inspection

```text
┌──────────────────────────────────── ASSET INSPECTION ───────────────────────────────────────┐
│ [Back] IMG_4821.JPG                                           [Verify] [Edit] [Reprocess]  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────┐  ┌───────────────────────────────────────────────────────┐ │
│ │                              │  │ Summary                                               │ │
│ │        Main asset view       │  │ Best time: 2024-12-28 18:14                          │ │
│ │                              │  │ Device: iPhone 14 Pro Max                            │ │
│ │ overlay toggles              │  │ Scene: hospital room?                                │ │
│ │ [OCR] [Objects] [Regions]    │  │ Objects: IV pole, bed, phone                         │ │
│ └──────────────────────────────┘  │ OCR: 3 text regions                                   │ │
│                                    ├───────────────────────────────────────────────────────┤ │
│                                    │ Timestamps / provenance                              │ │
│                                    │ Deterministic facts                                  │ │
│                                    │ AI inferences with confidence                        │ │
│                                    ├───────────────────────────────────────────────────────┤ │
│                                    │ OCR                                                  │ │
│                                    │ Full extracted text with regions                     │ │
│                                    ├───────────────────────────────────────────────────────┤ │
│                                    │ Review / notes / lineage                             │ │
│                                    └───────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 20. Security requirements for Version 1

Version 1 is private local software.

Security requirements:

- require authentication before showing application content,
- no public browsing,
- no anonymous routes exposing metadata,
- secrets stored outside repository,
- local transport and session handling should still be implemented properly,
- audit logs for important destructive actions,
- user corrections should be attributable to the authenticated local user session.

Cloud-specific measures such as CMEK are deferred with GCP deployment.

---

## 21. Data model direction

The exact schema can evolve, but the product should be designed around these main entity groups.

### 21.1 Core entities

- `asset`
- `asset_path_history`
- `asset_hash`
- `asset_metadata_raw`
- `asset_metadata_normalized`
- `asset_derivative`
- `asset_ocr`
- `asset_ocr_segment`
- `asset_object_detection`
- `asset_scene_inference`
- `asset_place_inference`
- `asset_time_inference`
- `asset_human_descriptor`
- `asset_animal_descriptor`
- `asset_duplicate_cluster`
- `asset_review_state`
- `collection`
- `tag`
- `job_run`
- `extractor_run`
- `manual_correction`

### 21.2 Schema rule

Raw extractor output and normalized metadata should never be the same table. Keep them separate.

### 21.3 Why that rule matters

This prevents schema fragility, preserves lineage, and makes reprocessing safer.

---

## 22. Performance requirements

Version 1 should feel operationally strong even on a large archive.

### 22.1 Required performance characteristics

- incremental scanning should avoid full rework when possible
- gallery should feel fast under large result sets
- thumbnails should load quickly
- extraction should work in bounded local batches
- failures should not crash whole pipeline runs
- jobs should be resumable where practical

### 22.2 Why batching matters

The user’s machine has strong but finite local resources. The pipeline should process assets in manageable units, especially for video and AI extraction.

---

## 23. Observability and diagnostics

The product must be debuggable.

Version 1 should include:

- structured logs
- job-level statuses
- extraction failure reasons
- counts by stage
- simple diagnostics dashboard or job screen
- ability to inspect raw extractor output for one asset

---

## 24. Testing strategy

Version 1 should include:

- unit tests for normalization logic
- integration tests for ingest pipeline
- sample fixture assets for regression testing
- prompt/output snapshot tests for extraction schemas where practical
- UI smoke tests for key flows

The point is not perfect coverage. The point is to make the pipeline stable enough for iterative issue-driven development.

---

## 25. Release definition for Version 1

Version 1 should be considered successful when all of the following are true:

1. The user can register local media roots without copying originals.
2. The system can index and persist metadata for large sets of photos and videos.
3. The system can extract rich metadata, OCR, scene information, object information, and time/place candidates.
4. The user can search and filter effectively in the web UI.
5. The user can inspect one asset with meaningful evidence and lineage.
6. The user can review uncertain results and apply corrections.
7. The user can rerun extraction safely.
8. The architecture remains clean enough to support later issue streams.

---

## 26. Deferred issue streams after Version 1

These are intentionally deferred, not forgotten.

### 26.1 Face detection and identity

A later issue stream can introduce:

- dedicated face detection
- face embeddings
- identity exemplars
- candidate matching
- person entity management

### 26.2 Local VLM fallback and expansion

A later issue stream can add:

- Qwen-VL or similar local models
- offline extraction policies
- hybrid routing by cost or asset type

### 26.3 GCP deployment

A later issue stream can add:

- Cloud Storage for originals/derivatives
- Cloud SQL PostgreSQL
- Cloud Run API/web
- Cloud Run Jobs for workers
- Google Identity auth flows
- CMEK for cloud resources

### 26.4 Knowledge graph and advanced relation views

A later issue stream can turn extracted metadata into richer graph exploration UX.

---

## 27. Delivery approach

The product should be built through issue-driven development.

Recommended execution pattern:

1. build the local foundation,
2. implement ingest and deterministic registration,
3. implement AI extraction contracts,
4. implement normalized metadata schema,
5. implement search and gallery,
6. implement review workflows,
7. harden reprocessing,
8. only then expand into later issue streams.

This keeps Version 1 coherent while still making it comprehensive.

---

## 28. Final product statement

This product is a **local-first private forensic media organizer** for a single user with a large archive of photos and videos. Its purpose is to turn those assets into a structured, evidence-backed, searchable knowledge system without moving originals. Version 1 should already be strong and comprehensive in metadata extraction, inspection, review, and reprocessing. Face identity and cloud deployment are valuable later additions, but they should not dilute the first release.
