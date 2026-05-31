from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import tarfile
from pathlib import Path


DEFAULT_SOURCE = Path("raw_example/demo_germany_energy_data")
DEFAULT_OUTPUT = Path("dist/demo_germany_energy_data.tar.gz")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic Loom tutorial data archive.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    archive_bytes = build_archive_bytes(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(archive_bytes)
    print(f"Wrote: {args.output}")
    print(f"SHA256: {hashlib.sha256(archive_bytes).hexdigest()}")
    return 0


def build_archive_bytes(source: Path) -> bytes:
    source = source.resolve()
    if not (source / "loom.md").exists():
        raise SystemExit(f"Missing tutorial dataset loom.md: {source / 'loom.md'}")

    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as gzip_file:
        with tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for path in sorted(source.rglob("*")):
                arcname = Path(source.name) / path.relative_to(source)
                info = archive.gettarinfo(str(path), arcname=str(arcname))
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                if path.is_file():
                    with path.open("rb") as file_obj:
                        archive.addfile(info, file_obj)
                else:
                    archive.addfile(info)
    return buffer.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
