# Deploy

This guide describes the current Render deployment for this repository.

If this document and `render.yaml` ever disagree, trust `render.yaml`.

## Current Services

- `loom-api-free`
  Render web service for `packages/loom-server`
- `loom-web`
  Render static site for `packages/loom-web`
- `loom-postgres`
  Render Postgres database

The frontend no longer builds from the repository root `web/` directory.
Render must build and publish from `packages/loom-web`.

## Current Blueprint

`render.yaml` currently defines:

- API
  - type: `web`
  - runtime: `python`
  - name: `loom-api-free`
  - plan: `starter`
  - build command: `pip install ./packages/loom-server`
  - start command: `loom-server run --storage-root /var/data/loom-server-storage --workspace-root /opt/render/project/src`
  - health check: `/health`
  - persistent disk mounted at `/var/data`
- Web
  - type: `web`
  - runtime: `static`
  - name: `loom-web`
  - build command: `cd packages/loom-web && corepack enable && pnpm install --frozen-lockfile && pnpm run build`
  - publish path: `./packages/loom-web/dist`
  - env: `VITE_API_BASE_URL=https://loom-api-free.onrender.com`
- Database
  - name: `loom-postgres`
  - plan: `free`

## Preferred Deploy Flow

Use the repository script:

```bash
uv run python scripts/deploy_render.py
```

Default behavior:

- requires a clean worktree
- requires `HEAD` to match `origin/<current-branch>`
- runs `render blueprints validate`
- deploys API and web
- verifies the live API and web endpoints

For frontend-only changes, deploy only the static site:

```bash
uv run python scripts/deploy_render.py --web-only
```

This still validates `render.yaml` first unless you pass `--skip-validate`.

## Useful Flags

```bash
uv run python scripts/deploy_render.py --api-only
uv run python scripts/deploy_render.py --web-only
uv run python scripts/deploy_render.py --allow-dirty
uv run python scripts/deploy_render.py --skip-validate
uv run python scripts/deploy_render.py --skip-verify
uv run python scripts/deploy_render.py --skip-remote-check
uv run python scripts/deploy_render.py --commit <sha>
```

## Manual Blueprint Check

```bash
render blueprints validate
```

If the Render CLI says your token is expired, refresh it before deploying:

```bash
render login
```

## Documentation Follow-up

If the Render workflow changes, update:

- `render.yaml`
- this file
- `README.md` if the top-level navigation changed
- `docs/user/*` or `packages/loom/README.md` if user-facing onboarding changed
- related maintainer skills
