from __future__ import annotations

import argparse
from pathlib import Path

from ..data import get as get_resource
from ..explore_repo import confirm_changes, ensure_explore_repo
from ..scanner import scan_all_topics_to_explore, scan_topic_to_explore
from ..server_config import persist_base_url
from ..sync_client import pull_raw_workspaces, pull_workspaces, push_workspaces
from .output import print_status_summary, print_workspace_status
from .skill import install_skills


def run_install(args: argparse.Namespace) -> int:
    workspace_root = args.workspace_root.resolve()
    installed_skills = install_skills(
        args.codex_home.resolve(),
        workspace_root,
        tuple(args.agents) if args.agents else None,
    )
    repo_dir = ensure_explore_repo(workspace_root)
    for skill in installed_skills:
        print(f"Installed Loom skill for {skill.agent}: {skill.path}")
    print(f"Initialized loom_explore git repo at: {repo_dir}")
    print(f"Initialized Loom workspace root at: {repo_dir.parent}")
    print("Agents can now use a fast path for commands like `loom scan energy`.")
    return 0


def run_scan(args: argparse.Namespace) -> int:
    if args.topic:
        _print_scan_result(scan_topic_to_explore(args.topic, args.workspace_root))
        print_status_summary(args.workspace_root, args.topic)
        return 0

    results = scan_all_topics_to_explore(args.workspace_root)
    if not results:
        loom_root = Path(args.workspace_root).resolve() / "loom" / "loom_raw"
        print(f"No workspaces found under: {loom_root}")
        return 0
    for result in results:
        _print_scan_result(result)
        print_status_summary(args.workspace_root, result.topic)
    return 0


def run_set_api(args: argparse.Namespace) -> int:
    base_url = persist_base_url(args.base_url)
    print(f"Default Loom API base URL set to: {base_url}")
    return 0


def run_get(args: argparse.Namespace) -> int:
    local_path = get_resource(args.resource, workspace_root=args.workspace_root, server_url=args.server_url)
    print(f"Cached resource: {args.resource}")
    print(f"Local path: {local_path}")
    return 0


def run_status(args: argparse.Namespace) -> int:
    print_workspace_status(args.workspace_root, args.workspace)
    return 0


def run_confirm(args: argparse.Namespace) -> int:
    commit_hash = confirm_changes(args.workspace_root, args.workspace, getattr(args, "message", None))
    if commit_hash is None:
        print("No pending changes to confirm.")
        return 0
    print(f"Confirmed changes for {args.workspace or 'all workspaces'}.")
    print(f"Commit: {commit_hash}")
    return 0


def run_push(args: argparse.Namespace) -> int:
    return _print_push_results(push_workspaces(args.workspace_root, args.server_url, args.workspace, args.message))


def run_pull(args: argparse.Namespace) -> int:
    return _print_pull_results(pull_workspaces(args.workspace_root, args.server_url, args.workspace))


def run_pull_raw(args: argparse.Namespace) -> int:
    results = pull_raw_workspaces(args.workspace_root, args.server_url, args.workspace)
    if not results:
        print("No remote workspaces found to pull raw files for.")
        return 0
    for result in results:
        print(f"Pulled raw workspace: {result.workspace}")
        print(f"Manifest files: {result.manifest_file_count}")
        print(f"Downloaded files: {result.downloaded_file_count}")
        print(f"Linked local files: {result.linked_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        if result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return 0


def _print_scan_result(result) -> None:
    print(f"Scanned topic: {result.topic}")
    print(f"Raw directory: {result.raw_topic_dir}")
    print(f"Explore directory: {result.explore_topic_dir}")
    print(f"Datasets discovered: {result.dataset_count}")
    print(f"Datasets rebuilt: {len(result.rebuilt_dataset_dirs)}")
    for dataset_dir in result.rebuilt_dataset_dirs:
        print(f"- rebuilt: {dataset_dir}")
    print(f"Datasets skipped: {len(result.skipped_dataset_dirs)}")
    for dataset_dir in result.skipped_dataset_dirs:
        print(f"- skipped: {dataset_dir}")
    if result.missing_dataset_dirs:
        print(f"Missing source datasets kept in explore: {len(result.missing_dataset_dirs)}")
        for relative_dir in result.missing_dataset_dirs:
            print(f"- kept: {relative_dir}")


def _print_push_results(results: tuple[object, ...]) -> int:
    if not results:
        print("No local workspaces found to push.")
        return 0
    exit_code = 0
    for result in results:
        if result.conflicted:
            exit_code = 1
            print(f"Push paused for workspace: {result.workspace}")
            print(f"Remote revision: {result.revision_id or '-'}")
            print("Conflict detected during rebase. Resolve the files below, then run:")
            print(f"  loom confirm {result.workspace}")
            print(f"  loom push {result.workspace}")
            for path in result.conflict_paths:
                print(f"- conflict: {path}")
            continue
        print(f"Pushed workspace: {result.workspace}")
        print(f"Revision: {result.revision_id}")
        print(f"Tree hash: {result.tree_hash}")
        print(f"Changed files: {result.changed_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        print(f"Raw objects uploaded: {result.raw_uploaded_object_count}")
        print(f"Raw path mappings changed: {result.raw_mapping_changed_count}")
        print(f"Raw path mappings deleted: {result.raw_mapping_deleted_count}")
        if result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return exit_code


def _print_pull_results(results: tuple[object, ...]) -> int:
    if not results:
        print("No remote workspaces found to pull.")
        return 0
    exit_code = 0
    for result in results:
        print(f"Pulled workspace: {result.workspace}")
        print(f"Revision: {result.revision_id}")
        print(f"Changed: {'yes' if result.changed else 'no'}")
        print(f"Changed files: {result.changed_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        if result.conflicted:
            exit_code = 1
            print("Conflict detected during rebase. Resolve the files below, then run:")
            print(f"  loom confirm {result.workspace}")
            print(f"  loom push {result.workspace}")
            for path in result.conflict_paths:
                print(f"- conflict: {path}")
        elif result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return exit_code
