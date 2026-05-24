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

            readme_path = workspace_dir / "README.md"
            datasets = self._list_datasets(workspace_dir)
            workspaces.append(
                {
                    "name": workspace_dir.name,
                    "dataset_count": len(datasets),
                    "datasets": datasets,
                    "readme_markdown": readme_path.read_text(encoding="utf-8") if readme_path.exists() else "",
                }
            )
        return workspaces

    def get_workspace(self, workspace: str) -> dict[str, object] | None:
        workspace_dir = self.workspace_root / workspace
        if not workspace_dir.exists() or not workspace_dir.is_dir():
            return None

        readme_path = workspace_dir / "README.md"
        datasets = self._list_datasets(workspace_dir)
        return {
            "name": workspace,
            "dataset_count": len(datasets),
            "readme_markdown": readme_path.read_text(encoding="utf-8") if readme_path.exists() else "",
            "datasets": datasets,
        }

    def _list_datasets(self, workspace_dir: Path) -> list[dict[str, object]]:
        datasets: list[dict[str, object]] = []
        for profile_path in sorted(workspace_dir.rglob("profile.json")):
            if profile_path.parent == workspace_dir:
                continue

            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            overview_path = profile_path.parent / "overview.md"
            dataset_relative_dir = profile_path.parent.relative_to(workspace_dir).as_posix()
            csv_profiles = self._load_csv_profiles(profile_path.parent, profile)

            datasets.append(
                {
                    "name": profile_path.parent.name,
                    "path": dataset_relative_dir,
                    "overview_markdown": overview_path.read_text(encoding="utf-8") if overview_path.exists() else "",
                    "source": profile.get("source", {}),
                    "csv_count": profile.get("csv_count", len(csv_profiles)),
                    "total_row_count": profile.get("total_row_count", 0),
                    "csv_files": profile.get("csv_files", []),
                    "csv_profiles": csv_profiles,
                }
            )
        return datasets

    def _load_csv_profiles(self, dataset_dir: Path, dataset_profile: dict[str, object]) -> list[dict[str, object]]:
        csv_profiles: list[dict[str, object]] = []
        for csv_entry in dataset_profile.get("csv_files", []):
            profile_name = csv_entry.get("profile_file")
            if not isinstance(profile_name, str):
                continue
            csv_profile_path = dataset_dir / profile_name
            if not csv_profile_path.exists():
                continue
            csv_profiles.append(json.loads(csv_profile_path.read_text(encoding="utf-8")))
        return csv_profiles


def build_explore_catalog(workspace_root: Path | str) -> ExploreCatalog:
    return ExploreCatalog(workspace_root=get_explore_repo_dir(workspace_root))
