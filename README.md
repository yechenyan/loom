# loom-data

`loom-data` helps agents work with large local datasets without reading every raw file up front.

## Start Here

- Canonical behavior and terminology:
  - `docs/reference/loom-reference.md`
- End-user guides:
  - `docs/user/quickstart.md`
  - `docs/user/chat-vs-cli.md`
  - `docs/user/workflows.md`
  - `docs/user/faq.md`
- Developer and maintainer guides:
  - `docs/dev/setup.md`
  - `docs/dev/architecture.md`
  - `docs/dev/release.md`
  - `docs/dev/deploy.md`
  - `docs/dev/documentation.md`
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
