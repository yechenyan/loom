---
name: loom-dataset-scan-review
description: Use when the user asks to scan local data into Loom, including `loom scan <path> [to <workspace>]`, `scan <path> with loom`, or requests to create searchable cards from local raw datasets. Always scan, then review and curate generated cards before calling the scan ready.
---

# loom-dataset-scan-review

Loom helps agents use project-local datasets: inspect lightweight cards in `./loom` first, fetch exact raw files only when needed, and answer source-backed data questions from raw data.

## Use This Skill

Use this skill when:

- The user writes `loom scan <path> [to <workspace>]`.
- The user writes `scan <path> with loom`.
- The user asks to scan local raw data into Loom.
- The user asks to create searchable cards, summaries, or an index for local datasets.

Do not use this skill when:

- The user only asks for a value or source-backed fact. Use `loom-local-data-lookup` instead.
- The user only asks for `status`, `confirm`, `push`, `pull`, or setup. Use `loom-workspace-ops` instead.
- The task is ordinary data-processing code and does not request a Loom scan.

## Names

- `loom scan ...` is a chat instruction. Do not run it in the shell.
- `loomcli scan-index ...` is the executable CLI scan command.

## Scan Workflow

Translate the user's chat intent into `loomcli scan-index` while preserving the source path and workspace exactly.

Pattern:

```text
loom scan <path> [to <workspace>]
```

Terminal command:

```bash
uv run loomcli scan-index <path> [to <workspace>]
```

Rules:

- Do not substitute the tutorial path unless the user asked for it.
- The source path is required.
- `to <workspace>` is optional.
- If no workspace is provided, Loom reuses the recent workspace or falls back to `temporary`.
- One workspace can track multiple source paths.
- Duplicate dataset paths stop the scan with an error; do not work around this by silently changing paths.

## Required Review

After `loomcli scan-index` finishes, do a real review before saying the scan is ready:

1. Read each scanned dataset's source `loom.md`.
2. Read generated `loom/<workspace>/README.md`.
3. Read each generated `overview.md`.
4. Review every CSV card for small datasets, or at least one representative card per CSV family for larger datasets.
5. Check that cards explain dataset purpose, source, key dimensions, scenario or year fields, units, and what each column is for.
6. If a summary is generic or misses context from `loom.md`, edit or supplement it before replying.
7. Say explicitly whether you completed a full review or only a spot check.
8. Do not suggest `loomcli confirm` unless review is complete or the user explicitly accepts a draft scan.

## Completion Standard

A scan is not ready just because `loomcli scan-index` succeeded. It is ready only after the generated cards are useful enough for later lookup tasks.
