---
name: loom-render-deploy
description: Use this skill when you need to deploy the current Loom frontend and backend changes to Render, validate the Blueprint, trigger the API and web deploys, and verify the live endpoints.
---

# Loom Render Deploy

Use this skill when the user asks to deploy, publish, or release the current repository changes to the existing Render services.

## What this handles

- Deploys the current pushed commit to:
  - `loom-api-free`
  - `loom-web`
- Validates `render.yaml` before triggering deploys.
- Verifies the live API and web URLs after Render finishes.

## Preflight

1. Read `git status --short` and `git branch --show-current`.
2. Make sure the commit to deploy has already been pushed to `origin/<current-branch>`.
3. If the worktree is dirty, either commit first or deliberately run the script with `--allow-dirty`.

## Standard command

Run this from the repository root:

```bash
uv run python scripts/deploy_render.py
```

Default behavior:

- requires a clean worktree
- requires `HEAD` to match `origin/<current-branch>`
- runs `render blueprints validate`
- deploys API first, then web
- waits for both deploys to finish
- checks:
  - `https://loom-api-free.onrender.com/health`
  - `https://loom-web.onrender.com`

## Useful flags

- Deploy only API:
  - `uv run python scripts/deploy_render.py --api-only`
- Deploy only web:
  - `uv run python scripts/deploy_render.py --web-only`
- Skip Blueprint validation:
  - `uv run python scripts/deploy_render.py --skip-validate`
- Skip remote branch check:
  - `uv run python scripts/deploy_render.py --skip-remote-check`
- Deploy a specific commit:
  - `uv run python scripts/deploy_render.py --commit <sha>`

## Failure handling

- If Blueprint validation fails, fix `render.yaml` before retrying.
- If Render deploy fails, inspect the failing service's deploy logs before retrying.
- If health verification fails after a `live` deploy, treat that as a real deploy problem instead of assuming success.

## Repo hygiene

- If the Render deployment workflow changes, update:
  - `wiki/deploy/readme.md`
  - `wiki/manule/readme.md`
  - `README.md` when maintainer guidance changes
