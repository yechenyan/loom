from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def blob_storage_path(storage_root: Path, file_sha256: str) -> Path:
    return storage_root / "blobs" / file_sha256[:2] / file_sha256[2:4] / file_sha256


def raw_blob_storage_path(storage_root: Path, file_sha256: str) -> Path:
    return storage_root / "raw-blobs" / file_sha256[:2] / file_sha256[2:4] / file_sha256


def compute_tree_hash(manifest: dict[str, dict[str, object]]) -> str:
    digest = sha256()
    for path in sorted(manifest):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(manifest[path]["sha256"]).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()
