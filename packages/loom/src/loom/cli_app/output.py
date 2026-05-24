from __future__ import annotations

from pathlib import Path

from ..explore_repo import get_repo_status
from ..sync_state import load_workspace_sync_state


def print_status_summary(workspace_root: Path | str, workspace: str) -> None:
    status = get_repo_status(workspace_root, workspace)
    if not status.entries:
        print("No pending changes detected after scan.")
        return
    launcher = Path(workspace_root).resolve() / "scripts" / "loom.py"
    print("Pending changes:")
    for entry in status.entries:
        print(f"{entry.code} {entry.path}")
    print(f"Confirm with: uv run python {launcher} confirm {workspace}")


def print_workspace_status(workspace_root: Path | str, workspace: str | None) -> None:
    status = get_repo_status(workspace_root, workspace)
    print(f"Explore repo: {status.repo_dir}")
    if status.scope:
        state = load_workspace_sync_state(workspace_root, status.scope)
        print(f"Workspace: {status.scope}")
        print(f"Last pulled revision: {state.last_pulled_revision or '-'}")
        print(f"Last pushed revision: {state.last_pushed_revision or '-'}")
        print(f"Last synced tree hash: {state.last_synced_tree_hash or '-'}")
        print(f"Last sync commit: {state.last_sync_commit or '-'}")
        if state.pending_rebase_revision:
            print(f"Pending rebase revision: {state.pending_rebase_revision}")
    if not status.entries:
        print("No pending changes.")
        return
    print("Pending changes:")
    for entry in status.entries:
        print(f"{entry.code} {entry.path}")
