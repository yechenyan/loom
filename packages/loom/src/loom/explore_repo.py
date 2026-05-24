from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RepoStatusEntry:
    code: str
    path: str


@dataclass(frozen=True)
class RepoStatus:
    repo_dir: Path
    scope: str | None
    entries: tuple[RepoStatusEntry, ...]


def get_explore_repo_dir(workspace_root: Path | str) -> Path:
    root = Path(workspace_root)
    return root / "test-project" / "loom" / "loom_explore"


def ensure_explore_repo(workspace_root: Path | str) -> Path:
    repo_dir = get_explore_repo_dir(workspace_root)
    repo_dir.mkdir(parents=True, exist_ok=True)
    _ensure_repo_gitignore(repo_dir)

    git_dir = repo_dir / ".git"
    if git_dir.exists():
        return repo_dir

    _run_git(repo_dir, ["init"])
    return repo_dir


def get_repo_status(workspace_root: Path | str, scope: str | None = None) -> RepoStatus:
    repo_dir = ensure_explore_repo(workspace_root)
    command = ["status", "--short", "--untracked-files=all"]
    if scope:
        command.extend(["--", scope])
    result = _run_git(repo_dir, command)

    entries: list[RepoStatusEntry] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        path = line[3:]
        entries.append(RepoStatusEntry(code=code, path=path))

    return RepoStatus(repo_dir=repo_dir, scope=scope, entries=tuple(entries))


def confirm_changes(workspace_root: Path | str, scope: str | None = None, message: str | None = None) -> str | None:
    repo_dir = ensure_explore_repo(workspace_root)
    status = get_repo_status(workspace_root, scope)
    if not status.entries:
        return None

    add_command = ["add", "-A"]
    if scope:
        add_command.extend(["--", scope])
    _run_git(repo_dir, add_command)

    commit_message = message or _default_commit_message(scope)
    result = _run_git(
        repo_dir,
        [
            "-c",
            "user.name=Loom",
            "-c",
            "user.email=loom@example.com",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            commit_message,
        ],
    )

    return get_repo_head_commit(workspace_root)


def get_repo_head_commit(workspace_root: Path | str) -> str | None:
    repo_dir = ensure_explore_repo(workspace_root)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def list_scope_commits_since(workspace_root: Path | str, scope: str, since_commit: str | None) -> tuple[str, ...]:
    repo_dir = ensure_explore_repo(workspace_root)
    command = ["rev-list", "--reverse"]
    if since_commit:
        command.append(f"{since_commit}..HEAD")
    else:
        command.append("HEAD")
    command.extend(["--", scope])
    result = _run_git(repo_dir, command)
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return tuple(commits)


def get_commit_file_map(workspace_root: Path | str, scope: str, commit: str) -> dict[str, bytes]:
    repo_dir = ensure_explore_repo(workspace_root)
    list_result = _run_git(repo_dir, ["ls-tree", "-r", "--name-only", commit, "--", scope])
    file_map: dict[str, bytes] = {}
    scope_prefix = f"{scope}/"
    for full_path in list_result.stdout.splitlines():
        normalized_path = full_path.strip()
        if not normalized_path:
            continue
        if normalized_path == scope:
            relative_path = Path(normalized_path).name
        elif normalized_path.startswith(scope_prefix):
            relative_path = normalized_path[len(scope_prefix) :]
        else:
            continue
        content = _run_git_bytes(repo_dir, ["show", f"{commit}:{normalized_path}"])
        file_map[relative_path] = content
    return file_map


def list_workspaces(workspace_root: Path | str) -> tuple[str, ...]:
    repo_dir = ensure_explore_repo(workspace_root)
    workspaces: list[str] = []
    for child in sorted(repo_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        workspaces.append(child.name)
    return tuple(workspaces)


def _default_commit_message(scope: str | None) -> str:
    if scope:
        return f"Confirm workspace {scope}"
    return "Confirm loom_explore changes"


def _extract_commit_hash(output: str) -> str | None:
    for token in output.replace("\n", " ").split():
        if len(token) >= 7 and all(character in "0123456789abcdef" for character in token.lower()):
            return token.strip("[]")
    return None


def _ensure_repo_gitignore(repo_dir: Path) -> None:
    gitignore_path = repo_dir / ".gitignore"
    required_lines = [".DS_Store"]

    existing_lines: list[str] = []
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()

    updated_lines = list(existing_lines)
    for line in required_lines:
        if line not in updated_lines:
            updated_lines.append(line)

    if updated_lines != existing_lines:
        gitignore_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _run_git(repo_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Unknown git error"
        raise RuntimeError(message)
    return result


def _run_git_bytes(repo_dir: Path, args: list[str]) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip() or result.stdout.decode(
            "utf-8", errors="replace"
        ).strip() or "Unknown git error"
        raise RuntimeError(message)
    return result.stdout
