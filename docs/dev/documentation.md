# Documentation Maintenance

This file defines how documentation is organized and maintained in this repository.

## Directory Contract

- `README.md`
  Repository landing page only.
- `AGENTS.md`
  Repository rules that agents should read before working.
- `docs/reference/`
  Canonical behavior and terminology.
- `docs/user/`
  User guides.
- `docs/dev/`
  Developer and maintainer guides.
- `tasks/`
  Active task notes.
- `tasks/history/`
  Completed task notes.

## Single Source Rule

For Loom behavior, terminology, and command semantics, the single written source of truth is:

- `docs/reference/loom-reference.md`

Other docs and skills should derive from it instead of redefining the same rules.

## Update Rules

- If code and docs disagree, trust the code.
- If Loom behavior changes, update `docs/reference/loom-reference.md` first.
- If top-level navigation changes, update `README.md`.
- If onboarding or usage guidance changes, update `docs/user/*` and `packages/loom/README.md` as needed.
- If user guidance changes, update `docs/user/*`.
- If developer workflow changes, update `docs/dev/*`.
- If package-facing guidance changes, update `packages/loom/README.md`.
- If agent behavior changes, update `AGENTS.md` and the related skills.

## File Size Rule

- Prefer keeping each code file and documentation file at 200 lines or fewer.
- No code file or documentation file should exceed 300 lines.
- If a file would exceed 300 lines, split it by responsibility instead of extending it further.

## Task Note Rules

- Put in-progress task notes under `tasks/`.
- When the user says the task is complete, summarize the result and move the note into `tasks/history/`.
- `tasks/history/` is historical reference, not source of truth for current behavior.
