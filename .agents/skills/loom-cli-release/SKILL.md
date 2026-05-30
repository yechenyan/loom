---
name: loom-cli-release
description: Use this skill when you need to publish a new loom-data CLI/package release from this repository, bump the version with scripts/release_pypi.py, run the built-in lint/test/build/publish flow, and manually verify PyPI visibility if needed after upload.
---

# Loom CLI Release

Use this skill when the user asks to publish, release, deploy, or ship a new `loom-data` CLI/package version from this repository.

## What to release

- The package name is `loom-data`.
- Version source of truth is the root `pyproject.toml`.
- Public terminal entrypoints currently come from `[project.scripts]`.

## Release flow

1. Read `pyproject.toml` and `git status --short`.
2. Confirm the latest published PyPI version before choosing the next version.
3. Make sure publish credentials are available through `UV_PUBLISH_TOKEN`, `PYPI_TOKEN`, or `[pypi].token` in `config/local.toml`.
4. Run the repository release script:
   - Patch release: `uv run python scripts/release_pypi.py patch`
   - Explicit release: `uv run python scripts/release_pypi.py X.Y.Z`
5. Let the script handle lint, minimal tests, build, and `uv publish`.
6. If you need post-publish verification, check PyPI manually after upload.

## Failure handling

- If lint or the minimal release tests fail, fix the blocking issue first, then rerun the release script.
- `scripts/release_pypi.py` restores `pyproject.toml` on failure unless explicitly told not to.
- If network access is sandboxed, request escalation rather than guessing the published version.

## Verification notes

- PyPI JSON and simple index can lag behind a successful upload.
- If upload succeeds but PyPI still shows the old version, report that the release request succeeded and note that public index refresh is still pending.
- Local `pyproject.toml` and `uv.lock` version bumps are expected release artifacts.

## Repo hygiene

- If the CLI naming, release workflow, or maintainer instructions changed, update:
  - `docs/reference/loom-reference.md`
  - `docs/dev/release.md`
  - `packages/loom/README.md` when package-facing guidance changed
  - `README.md` when top-level navigation changed
