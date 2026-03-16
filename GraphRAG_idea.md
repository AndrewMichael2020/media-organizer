GraphRAG and pageIndex applicability
These are genuinely useful fits for this app. Here's where each would land:

GraphRAG — strong fit for search
Your schema is already pre-structured for graph queries. The key tables form a natural entity-relationship graph:

What GraphRAG enables that flat SQL cannot:

Query type Example
Multi-hop co-occurrence "Find all assets where a vehicle appears in a rainy urban scene" (joins 3 extracted tables)
Community detection "What events / trips exist in this archive?" — temporal + location + object clustering
Evidence chains "Where has this specific object appeared across time?"
Global thematic queries "What recurring themes appear in this archive?" — requires summarizing the whole corpus
Practical V1 path (no new infra): PostgreSQL already supports this via WITH RECURSIVE CTEs and multi-table joins on the existing schema. The assertion table with predicate/value/source is exactly a knowledge graph edge store — queries like WHERE predicate = 'contains_object' are trivial joins.

V2 GraphRAG path: Microsoft's GraphRAG library builds communities from extracted text. You'd feed it one document per asset (concatenating ocr_document.full_text + scene_summary.description + object labels + place names). It would discover event clusters automatically without explicit labeling.

pageIndex — the right abstraction for search
"pageIndex" in the GraphRAG sense means treating each asset's extracted text as a text unit (a page). For this app:

One document per asset = all extracted text fields concatenated (full_text, description, object label values, place name values, assertion.value where type is text)
Index = PostgreSQL tsvector for V1 (full-text search, zero new dependencies)
Index = pgvector embeddings for semantic similarity ("find photos that look/feel like this one")
Concrete search implementation sketch:

Recommended sequencing:

tsvector full-text search first (zero new deps, immediate value)
Add pgvector extension for semantic similarity (one CREATE EXTENSION)
Add graph-style multi-hop queries as structured filter builders
GraphRAG community detection as an optional enrichment job (V2)
Next suggested customizations
/create-instruction for search — file-scoped instructions for the \*_/_.py files under the search package, describing the three-layer index design once implemented
/create-prompt for search-implementation — a focused prompt that generates the full search implementation given the schema context above, so you can invoke it cleanly as /search-implementation
