# Deploy

This guide describes the current Render deployment for this repository.

If this document and `render.yaml` ever disagree, trust `render.yaml`.

## Current Services

- `loom-api-free`
  Render web service for `packages/loom-server`
- `loom-web`
  Render static site for `web`
- `loom-postgres`
  Render Postgres database

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
  - build command: `cd web && npm ci && npm run build`
  - publish path: `./web/dist`
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

## Documentation Follow-up

If the Render workflow changes, update:

- `render.yaml`
- this file
- `README.md` if the top-level navigation changed
- `docs/user/*` or `packages/loom/README.md` if user-facing onboarding changed
- related maintainer skills
