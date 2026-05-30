# Loom Agent Rules

Read this file before making changes in this repository.

## Repository Rules

- Code is the source of truth.
- If docs disagree with code, fix the docs.
- The canonical Loom behavior document is `docs/reference/loom-reference.md`.
- Prefer keeping any code file or documentation file at 200 lines or fewer.
- No code file or documentation file should exceed 300 lines.
- If a file would exceed 300 lines, split it into smaller files.

## Documentation Layout

- `README.md`
  Landing page and navigation only.
- `docs/reference/`
  Canonical behavior and terminology.
- `docs/user/`
  User-facing guides.
- `docs/dev/`
  Developer and maintainer guides.
- `tasks/`
  Active task notes.
- `tasks/history/`
  Completed task notes.

## Required Documentation Checks

After changing code, decide whether to update:

- `docs/reference/loom-reference.md`
- `docs/user/*`
- `docs/dev/*`
- `README.md`
- `packages/loom/README.md`
- related skills under `.agents/skills/`

## Task Archiving

- If the user says a task is complete, summarize the request and outcome.
- Move the corresponding note into `tasks/history/`.
- Do not use task-history notes as current product truth.
