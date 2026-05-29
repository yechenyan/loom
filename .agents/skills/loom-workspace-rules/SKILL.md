---
name: loom-workspace-rules
description: Use this skill for any task performed inside the loom repository. Update wiki/manule/readme.md and README when commands, workflows, outputs, install steps, or behavior change; treat code as the source of truth over wiki/history notes; when a user says a task is complete, move the matching note from wiki/task to wiki/history and add a concise implementation summary; never read wiki/discard; keep code files under 200 lines and remove unused files instead of leaving dead files around.
---

# Loom Workspace Rules

Use these rules for any work in this repository.

## Documentation

- When a feature, command, install step, usage pattern, workflow, or behavior changes, update `wiki/manule/readme.md`.
- Keep `README.md` practical and onboarding-friendly.
- If behavior changes, update output descriptions and recommended workflow docs too.
- `wiki/history/` is reference material only. If it disagrees with the code, trust the code.

## Task Completion

- When the user says the current task is complete, move the related note from `wiki/task/` into `wiki/history/`.
- Preserve the original request in the moved history file.
- Add a concise summary of what was implemented, changed, or decided.

## Repository Boundaries

- Do not read `wiki/discard`.
- No code file may exceed 200 lines.
- Remove unused files instead of leaving dead code or generated leftovers in the repo.
