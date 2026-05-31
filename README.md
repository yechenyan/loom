# loom-data

`loom-data` helps agents work with large local datasets without reading every raw file up front.

## Start Here

- Canonical behavior and terminology:
  - `docs/reference/loom-reference.md`
- End-user guides:
  - `docs/user/00-overview.md`
  - `docs/user/01-quickstart.md`
  - `docs/user/02-workspaces.md`
  - `docs/user/03-scan-and-review.md`
  - `docs/user/04-ask-and-fetch.md`
  - `docs/user/05-sync-and-raw-cache.md`
  - `docs/user/06-python-api.md`
  - `docs/user/07-command-reference.md`
  - `docs/user/08-faq.md`
- Developer and maintainer guides:
  - `docs/dev/setup.md`
  - `docs/dev/architecture.md`
  - `docs/dev/release.md`
  - `docs/dev/deploy.md`
  - `docs/dev/documentation.md`
  - `docs/dev/demo-data.md`
- Package usage guide:
  - `packages/loom/README.md`
- Agent repository rules:
  - `AGENTS.md`

## Core Model

- `loom ...`
  Chat instructions sent to an agent.
- `loomcli ...`
  Explicit terminal commands.
- `import loom`
  Python package import.

If any document disagrees with the code, trust the code and then update `docs/reference/loom-reference.md`.
