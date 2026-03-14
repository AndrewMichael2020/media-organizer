from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).parents[4]  # apps/api/app/core/config.py → 4 levels up = repo root
# Load .env into os.environ early so background threads (GeminiProvider etc.) can read all vars
load_dotenv(_REPO_ROOT / ".env", override=False)


def _load_yaml_config() -> dict:
    """Merge default.yaml with local.yaml (local takes precedence)."""
    root = _REPO_ROOT
    config_dir = root / "config"

    cfg: dict = {}
    for name in ("default.yaml", "local.yaml"):
        path = config_dir / name
        if path.exists():
            with path.open() as f:
                data = yaml.safe_load(f) or {}
            cfg = _deep_merge(cfg, data)
    return cfg


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),  # absolute path to repo root .env
        env_prefix="FMO_",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql://fmo:fmo@localhost:5432/fmo",
        description="PostgreSQL DSN",
    )

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Model
    model_provider: str = "gemini"
    model_name: str = "gemini-3.1-flash-lite-preview"

    # Storage
    source_roots: list[str] = []
    derivative_cache_root: str = "/tmp/fmo_cache"

    # Worker
    worker_concurrency: int = 2

    def model_post_init(self, _context: object) -> None:
        """Overlay YAML config values that aren't set via env."""
        yaml_cfg = _load_yaml_config()

        for section, values in yaml_cfg.items():
            if isinstance(values, dict):
                for key, val in values.items():
                    attr = f"{section}_{key}"
                    if attr in self.model_fields and not os.environ.get(f"FMO_{attr.upper()}"):
                        object.__setattr__(self, attr, val)
            else:
                if section in self.model_fields and not os.environ.get(f"FMO_{section.upper()}"):
                    object.__setattr__(self, section, values)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
