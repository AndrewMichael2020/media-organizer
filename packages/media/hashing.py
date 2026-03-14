"""
Hashing adapter — SHA-256 canonical identity + perceptual hash (pHash).
Persists results to asset_hash table. Restartable (skips already-computed hashes).
"""
from __future__ import annotations

import hashlib
import logging
import sys
from pathlib import Path

import imagehash
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[2] / "db"))
from models import Asset, AssetHash  # noqa: E402
from session import get_session  # noqa: E402

logger = logging.getLogger(__name__)


def compute_sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def compute_phash(path: Path) -> str | None:
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def hash_asset(session: Session, asset: Asset) -> dict[str, str]:
    """Compute and persist hashes for one asset. Returns {hash_type: hash_value}."""
    path = Path(asset.canonical_path)
    if not path.exists():
        raise FileNotFoundError(path)

    existing = {
        h.hash_type: h.hash_value
        for h in session.scalars(
            select(AssetHash).where(AssetHash.asset_id == asset.id)
        ).all()
    }
    results: dict[str, str] = dict(existing)

    # SHA-256
    if "sha256" not in existing:
        value = compute_sha256(path)
        session.add(AssetHash(asset_id=asset.id, hash_type="sha256", hash_value=value))
        results["sha256"] = value
        logger.debug("sha256 %s → %s", asset.filename, value[:12])

    # pHash (photos only)
    if "phash" not in existing and asset.media_type == "photo":
        value = compute_phash(path)
        if value:
            session.add(AssetHash(asset_id=asset.id, hash_type="phash", hash_value=value))
            results["phash"] = value

    return results


def hash_all_pending(limit: int = 500) -> tuple[int, int]:
    """Hash all assets that don't yet have a sha256. Returns (done, errors)."""
    done = errors = 0
    with get_session() as session:
        # Assets without sha256
        hashed_ids = select(AssetHash.asset_id).where(AssetHash.hash_type == "sha256")
        assets = session.scalars(
            select(Asset)
            .where(Asset.id.not_in(hashed_ids), Asset.is_missing == False)  # noqa: E712
            .limit(limit)
        ).all()

        for asset in assets:
            try:
                hash_asset(session, asset)
                done += 1
            except Exception as exc:
                logger.warning("Hash failed for %s: %s", asset.canonical_path, exc)
                errors += 1

    return done, errors
