from __future__ import annotations

from datetime import datetime, timezone

from .local_sources import find_local_notice_dir, find_local_scan_source_file


def detect_local_raw_conflicts(workspace_root, workspace: str, remote_manifest):
    from hashlib import sha256

    conflicts: list[dict[str, str | int]] = []
    for relative_path, item in sorted(remote_manifest.items()):
        local_path = find_local_scan_source_file(workspace_root, workspace, relative_path)
        if local_path is None:
            continue
        local_sha256 = sha256(local_path.read_bytes()).hexdigest()
        if local_sha256 == str(item["sha256"]):
            continue
        conflicts.append({"path": relative_path, "local_sha256": local_sha256, "remote_sha256": str(item["sha256"]), "local_path": str(local_path)})
    return tuple(conflicts)


def write_raw_conflict_notice(workspace_root, workspace: str, conflicts):
    if not conflicts:
        return None
    notice_dir = find_local_notice_dir(workspace_root, workspace)
    if notice_dir is None:
        return None
    notice_path = notice_dir / "loom.raw-conflict.md"
    lines = ["# Loom Raw Conflict Notice", "", "Local raw files differ from the latest server manifest. Loom did not overwrite `raw_data`.", "", f"Generated at: {datetime.now(timezone.utc).isoformat()}", "", "Resolve these files manually if you want local raw sources to match the server:", ""]
    for item in conflicts:
        lines.extend([f"- path: {item['path']}", f"  - local sha256: {item['local_sha256']}", f"  - remote sha256: {item['remote_sha256']}", f"  - local file: {item['local_path']}"])
    lines.extend(["", "Suggested next steps:", "", "1. Review the local raw file and the synced explore output.", "2. Decide whether to keep the local raw file or align it with the server version.", "3. Re-run `loom scan`, then `loom confirm` if you intentionally keep the local version.", ""])
    notice_path.parent.mkdir(parents=True, exist_ok=True)
    notice_path.write_text("\n".join(lines), encoding="utf-8")
    return notice_path
