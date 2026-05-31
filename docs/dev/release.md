# Release

Use this guide when publishing a new `loom-data` package release.

## Source of Truth

- Version source: `pyproject.toml`
- Release script: `scripts/release_pypi.py`
- Publish credential sources:
  - `UV_PUBLISH_TOKEN`
  - `PYPI_TOKEN`
  - `[pypi].token` in `config/local.toml`

## Standard Flow

1. Check `git status --short`.
2. Confirm the next version.
3. Ensure the tutorial data archive is committed and reachable at the configured
   tag URL before publishing. The release script rebuilds
   `dist/demo_germany_energy_data.tar.gz` and refuses to publish if the
   configured URL is missing or its SHA256 does not match the CLI config.
4. Run:

```bash
uv run python scripts/release_pypi.py patch
```

Or:

```bash
uv run python scripts/release_pypi.py X.Y.Z
```

5. Let the script handle lint, minimal tests, tutorial asset verification,
   build, and publish.
6. If you need post-publish verification, check the package index manually after upload.

If the tutorial archive check fails, push the built archive to the configured
repository tag path or update the tutorial URL and SHA before rerunning the
release. Do not publish a CLI package whose default tutorial URL returns 404.

## Documentation Follow-up

If release-facing behavior or naming changed, update:

- `docs/reference/loom-reference.md`
- `docs/user/*` when onboarding or usage guidance changed
- `packages/loom/README.md`
- `README.md` when top-level navigation changed
- related skills when agent guidance changed
