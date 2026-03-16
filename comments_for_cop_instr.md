## Build and run commands

```bash
# Start PostgreSQL (Docker required)
bash scripts/db-start.sh          # docker compose up -d postgres (port 5432)

# Run database migrations
bash scripts/db-migrate.sh        # alembic upgrade head in packages/db/

# Start API server (port 8000, hot-reload)
bash scripts/api-start.sh         # uv run uvicorn app.main:app --reload

# Start web frontend (port 3000)
bash scripts/web-start.sh         # npm run dev in apps/web/

# All-in-one (macOS Terminal tabs)
bash scripts/dev.sh
```

**Python runtime:** `uv` (not pip). Each app and package is a separate uv project.
**Install deps:** `cd apps/api && uv sync` (or the relevant app/package dir).
**No global test runner yet** — test fixtures are in `tests/fixtures/`. Add tests alongside features.

## Config override

Copy `config/local.yaml.example` → `config/local.yaml` and set `storage.source_roots` and API keys.
Override individual values with `FMO_*` env vars (highest precedence). See `apps/api/app/core/config.py`.

## Current implementation status

| Package | Status |
|---------|--------|
| `packages/db` | Complete — all V1 tables, migrations, repositories |
| `packages/media` | Complete — exiftool, ffprobe, hashing, thumbnails |
| `packages/models` | Complete — gemini, deepinfra, lmstudio providers |
| `packages/vision` | Complete — image extraction pipeline |
| `packages/storage` | Complete — filesystem scanner |
| `packages/core` | **Stub** — only prints hello, no domain types yet |
| `packages/ocr` | **Not implemented** |
| `packages/search` | **Not implemented** — next priority |
| `apps/worker` | **Stub** — jobs run as FastAPI BackgroundTasks in apps/api |

## Package import convention

Packages are not installed as editable installs across apps. They use `sys.path.insert` at module load time:
```python
sys.path.insert(0, str(Path(__file__).parents[N] / "packages" / "db"))
```
When adding new cross-package imports, follow this pattern. Do not attempt to add packages as editable installs without checking the uv workspace configuration.