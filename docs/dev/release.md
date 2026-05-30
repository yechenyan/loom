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
3. Run:

```bash
uv run python scripts/release_pypi.py patch
```

Or:

```bash
uv run python scripts/release_pypi.py X.Y.Z
```

4. Let the script handle lint, minimal tests, build, and publish.
5. If you need post-publish verification, check the package index manually after upload.

## Documentation Follow-up

If release-facing behavior or naming changed, update:

- `docs/reference/loom-reference.md`
- `docs/user/*` when onboarding or usage guidance changed
- `packages/loom/README.md`
- `README.md` when top-level navigation changed
- related skills when agent guidance changed
