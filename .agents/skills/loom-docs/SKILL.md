---
name: loom-docs
description: Use this skill when you need to maintain Loom repository documentation, explain the documentation structure, or decide which docs must change after a code change.
---

# Loom Docs

Use this skill whenever the task is about repository documentation structure, documentation cleanup, or deciding which docs need updates after code changes.

Start by reading:

- `AGENTS.md`
- `docs/reference/loom-reference.md`
- `docs/dev/documentation.md`

## Documentation Structure

- `README.md`
  Landing page and navigation only.
- `docs/reference/`
  Canonical behavior and terminology.
- `docs/user/`
  User-facing usage guides.
- `docs/dev/`
  Developer and maintainer guides.
- `tasks/`
  Active task notes.
- `tasks/history/`
  Completed task notes.

## File Size Rule

- Prefer keeping each code file and documentation file at 200 lines or fewer.
- No code file or documentation file should exceed 300 lines.
- If a file would exceed 300 lines, split it into smaller files by responsibility.

## Single Source Rule

For Loom behavior and usage semantics, the written source of truth is:

- `docs/reference/loom-reference.md`

If code disagrees with the reference, trust the code and then update the reference first.

## What to Update After Code Changes

- Behavior, naming, CLI commands, chat semantics:
  - update `docs/reference/loom-reference.md`
- Top-level navigation:
  - update `README.md`
- Onboarding or usage guidance:
  - update `docs/user/*`
  - update `packages/loom/README.md` when package-facing guidance changed
- User workflow changes:
  - update `docs/user/*`
- Developer, release, deploy, or maintenance workflow changes:
  - update `docs/dev/*`
- Package-facing summary changes:
  - update `packages/loom/README.md`
- Agent workflow or repository rule changes:
  - update `AGENTS.md` and related skills

## Task Completion Rule

If the user says the current task is complete:

1. Summarize the original request and the implemented outcome.
2. Put or move the task note into `tasks/history/`.
3. Treat that history note as reference only, not as the current behavior source of truth.
