from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
DEFAULT_CONFIG_PATH = ROOT / "config" / "local.toml"
MINIMAL_TESTS = [
    "tests/test_server_config.py",
    "tests/test_set_api_command.py",
    "tests/test_packaging_metadata.py",
    "tests/test_release_checks.py",
]
LINT_TARGETS = [
    "packages/loom/src/loom",
    "scripts/release_pypi.py",
    "scripts/release_checks.py",
]
VERSION_RE = re.compile(r'(?m)^(version\s*=\s*")(\d+\.\d+\.\d+)(")$')

from release_checks import ReleaseCheckError, verify_tutorial_release_asset  # noqa: E402


class ReleaseError(RuntimeError):
    """Raised when the release workflow cannot continue safely."""


@dataclass(frozen=True)
class ReleaseConfig:
    version: str
    dry_run: bool
    test_pypi: bool
    skip_lint: bool
    skip_test: bool
    skip_publish: bool
    keep_version_on_failure: bool
    config_path: Path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bump the loom-data version, lint, test, build, and publish to PyPI.",
    )
    parser.add_argument(
        "target",
        help="Version bump target: patch, minor, major, or an explicit X.Y.Z version.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to the local private TOML config. Default: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and run uv publish in dry-run mode without uploading.",
    )
    parser.add_argument(
        "--test-pypi",
        action="store_true",
        help="Publish to TestPyPI instead of PyPI.",
    )
    parser.add_argument(
        "--skip-lint",
        action="store_true",
        help="Skip ruff lint checks.",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip the minimal release regression tests.",
    )
    parser.add_argument(
        "--skip-publish",
        action="store_true",
        help="Stop after a successful build without publishing.",
    )
    parser.add_argument(
        "--keep-version-on-failure",
        action="store_true",
        help="Do not restore pyproject.toml if a later release step fails.",
    )
    return parser.parse_args(argv)


def load_pyproject_text() -> str:
    return PYPROJECT.read_text(encoding="utf-8")


def read_current_version(pyproject_text: str) -> str:
    match = VERSION_RE.search(pyproject_text)
    if match is None:
        raise ReleaseError(f"Could not find [project].version in {PYPROJECT}")
    return match.group(2)


def bump_version(current: str, target: str) -> str:
    major, minor, patch = (int(part) for part in current.split("."))
    if target == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if target == "minor":
        return f"{major}.{minor + 1}.0"
    if target == "major":
        return f"{major + 1}.0.0"
    if re.fullmatch(r"\d+\.\d+\.\d+", target):
        return target
    raise ReleaseError("target must be patch, minor, major, or an explicit X.Y.Z version")


def write_version(pyproject_text: str, version: str) -> str:
    updated_text, replacements = VERSION_RE.subn(rf"\g<1>{version}\g<3>", pyproject_text, count=1)
    if replacements != 1:
        raise ReleaseError(f"Could not update version in {PYPROJECT}")
    PYPROJECT.write_text(updated_text, encoding="utf-8")
    return updated_text


def read_config_token(config_path: Path) -> str:
    if not config_path.exists():
        return ""

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    pypi = data.get("pypi", {})
    if isinstance(pypi, dict):
        token = pypi.get("token", "")
        if isinstance(token, str):
            return token.strip()
    return ""


def resolve_token(config_path: Path) -> str:
    for name in ("UV_PUBLISH_TOKEN", "PYPI_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value

    token = read_config_token(config_path)
    if token:
        return token

    raise ReleaseError(
        "Missing PyPI token. Set UV_PUBLISH_TOKEN or PYPI_TOKEN, or write [pypi].token to "
        f"{config_path}."
    )


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print(f"+ {shlex.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def clean_build_artifacts() -> None:
    for path in (ROOT / "dist", ROOT / "build"):
        if path.exists():
            shutil.rmtree(path)


def build_config(args: argparse.Namespace, current_version: str) -> ReleaseConfig:
    next_version = bump_version(current_version, args.target)
    return ReleaseConfig(
        version=next_version,
        dry_run=args.dry_run,
        test_pypi=args.test_pypi,
        skip_lint=args.skip_lint,
        skip_test=args.skip_test,
        skip_publish=args.skip_publish,
        keep_version_on_failure=args.keep_version_on_failure,
        config_path=Path(args.config).expanduser(),
    )


def release(config: ReleaseConfig, original_text: str) -> None:
    current_version = read_current_version(original_text)
    if config.version == current_version:
        print(f"Version remains {current_version}", flush=True)
    else:
        write_version(original_text, config.version)
        print(f"Bumped version: {current_version} -> {config.version}", flush=True)

    if not config.skip_lint:
        run(["uv", "tool", "run", "ruff", "check", *LINT_TARGETS])

    if not config.skip_test:
        run(["uv", "run", "pytest", *MINIMAL_TESTS])

    if not config.skip_publish:
        tutorial_asset = verify_tutorial_release_asset()
        print(
            "Verified tutorial release asset: "
            f"{tutorial_asset.url} "
            f"({tutorial_asset.size_bytes} bytes, sha256={tutorial_asset.sha256})",
            flush=True,
        )

    clean_build_artifacts()
    run(["uv", "build"])

    if config.skip_publish:
        print("Skipped publish step by request.", flush=True)
        return

    token = resolve_token(config.config_path)
    env = os.environ.copy()
    env["UV_PUBLISH_TOKEN"] = token
    publish_cmd = ["uv", "publish"]
    if config.dry_run:
        publish_cmd.append("--dry-run")
    if config.test_pypi:
        publish_cmd.extend(["--publish-url", "https://test.pypi.org/legacy/"])
    run(publish_cmd, env=env)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    original_text = load_pyproject_text()
    current_version = read_current_version(original_text)
    config = build_config(args, current_version)

    try:
        release(config, original_text)
    except (ReleaseError, ReleaseCheckError, subprocess.CalledProcessError) as exc:
        if not config.keep_version_on_failure and PYPROJECT.read_text(encoding="utf-8") != original_text:
            PYPROJECT.write_text(original_text, encoding="utf-8")
            print(f"Restored {PYPROJECT.name} to version {current_version}", flush=True)
        print(f"Release failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
