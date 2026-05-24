from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


def get_explore_repo_dir(workspace_root: Path | str) -> Path:
    return Path(workspace_root) / "loom" / "loom_explore"


@dataclass(frozen=True)
class ExploreCatalog:
    workspace_root: Path

    def list_workspaces(self) -> list[dict[str, object]]:
        workspaces: list[dict[str, object]] = []
        if not self.workspace_root.exists():
            return workspaces

        for workspace_dir in sorted(self.workspace_root.iterdir()):
            if not workspace_dir.is_dir() or workspace_dir.name.startswith("."):
                continue

            workspaces.append(build_workspace_payload_from_file_map(workspace_dir.name, _load_workspace_file_map(workspace_dir)))
        return workspaces

    def get_workspace(self, workspace: str) -> dict[str, object] | None:
        workspace_dir = self.workspace_root / workspace
        if not workspace_dir.exists() or not workspace_dir.is_dir():
            return None

        return build_workspace_payload_from_file_map(workspace, _load_workspace_file_map(workspace_dir))

    def _load_csv_profiles(self, dataset_dir: Path, dataset_profile: dict[str, object]) -> list[dict[str, object]]:
        return _load_csv_profiles_from_file_map(
            {
                path.relative_to(dataset_dir).as_posix(): path.read_text(encoding="utf-8")
                for path in sorted(dataset_dir.rglob("*"))
                if path.is_file()
            },
            dataset_profile,
        )


def build_workspace_payload_from_file_map(workspace: str, file_map: dict[str, str]) -> dict[str, object]:
    datasets = _list_datasets_from_file_map(file_map)
    return {
        "name": workspace,
        "dataset_count": len(datasets),
        "readme_markdown": file_map.get("README.md", ""),
        "datasets": datasets,
    }


def _load_workspace_file_map(workspace_dir: Path) -> dict[str, str]:
    file_map: dict[str, str] = {}
    for path in sorted(workspace_dir.rglob("*")):
        if not path.is_file():
            continue
        file_map[path.relative_to(workspace_dir).as_posix()] = path.read_text(encoding="utf-8")
    return file_map


def _list_datasets_from_file_map(file_map: dict[str, str]) -> list[dict[str, object]]:
    datasets: list[dict[str, object]] = []
    for relative_path in sorted(file_map):
        if relative_path == "profile.json" or not relative_path.endswith("/profile.json"):
            continue

        dataset_relative_dir = relative_path[: -len("/profile.json")]
        profile = json.loads(file_map[relative_path])
        dataset_file_map = {
            path[len(dataset_relative_dir) + 1 :]: content
            for path, content in file_map.items()
            if path.startswith(f"{dataset_relative_dir}/")
        }
        csv_profiles = _load_csv_profiles_from_file_map(dataset_file_map, profile)
        datasets.append(
            {
                "name": Path(dataset_relative_dir).name,
                "path": dataset_relative_dir,
                "overview_markdown": file_map.get(f"{dataset_relative_dir}/overview.md", ""),
                "source": profile.get("source", {}),
                "csv_count": profile.get("csv_count", len(csv_profiles)),
                "total_row_count": profile.get("total_row_count", 0),
                "csv_files": profile.get("csv_files", []),
                "csv_profiles": csv_profiles,
            }
        )
    return datasets


def _load_csv_profiles_from_file_map(file_map: dict[str, str], dataset_profile: dict[str, object]) -> list[dict[str, object]]:
    csv_profiles: list[dict[str, object]] = []
    for csv_entry in dataset_profile.get("csv_files", []):
        profile_name = csv_entry.get("profile_file")
        if not isinstance(profile_name, str):
            continue
        profile_content = file_map.get(profile_name)
        if profile_content is None:
            continue
        csv_profiles.append(json.loads(profile_content))
    return csv_profiles


def build_explore_catalog(workspace_root: Path | str) -> ExploreCatalog:
    return ExploreCatalog(workspace_root=get_explore_repo_dir(workspace_root))
