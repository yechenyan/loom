---
name: loom-workspace-rules
description: Use this skill for any task performed inside the loom repository. Read AGENTS.md and the Loom reference docs first, treat code as the source of truth, keep tasks under tasks/ and tasks/history/, prefer files at 200 lines or fewer, and split any file that would exceed 300 lines.
---

# Loom Workspace Rules

Use these rules for any work in this repository.

## Documentation

- Start by reading `AGENTS.md`.
- For Loom behavior changes, update `docs/reference/loom-reference.md` first.
- Keep `README.md` as a landing page and navigation hub.
- Update `docs/user/` and `docs/dev/` when their workflows change.
- `tasks/history/` is reference material only. If it disagrees with the code, trust the code.

## Task Completion

- When the user says the current task is complete, move the related note from `tasks/` into `tasks/history/`.
- Preserve the original request in the moved history file.
- Add a concise summary of what was implemented, changed, or decided.

## Repository Boundaries

- Prefer keeping code files and documentation files at 200 lines or fewer.
- No code file or documentation file may exceed 300 lines.
- If a file would exceed 300 lines, split it into smaller files.
- Remove unused files instead of leaving dead code or generated leftovers in the repo.
