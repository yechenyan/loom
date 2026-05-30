---
name: loom-local-data-lookup
description: Use when the user explicitly asks `loom ask ...` or `loom <question>`, or when modeling, coding, writing docs, or writing a paper requires project-local, source-backed dataset facts such as values, units, assumptions, parameters, CSV contents, or provenance.
---

# loom-local-data-lookup

Loom helps agents use project-local datasets: inspect lightweight cards in `./loom` first, fetch exact raw files only when needed, and answer source-backed data questions from raw data.

## Use This Skill

Use this skill when:

- The user writes `loom ask <question>`.
- The user writes bare `loom <question>`.
- The user asks you to use Loom to look up data.
- The user is modeling, coding, writing docs, or writing a paper and needs project-local data facts: values, units, assumptions, parameters, costs, provenance, CSV contents, or dataset fields.

Do not use this skill when:

- The user writes `loom scan`, `loom status`, `loom confirm`, `loom push`, or `loom pull`.
- The user writes unsupported chat forms such as `loom init`, `loom get`, `loom set-api`, or `loom install`.
- The task is ordinary Pandas, SQL, plotting, or data-processing code without a need to look up local source data.
- The user asks for a general concept explanation.
- The user asks for external, live, or web data.
- The user already provided the complete data needed and no local source file lookup is required.

## Names

- `loom ...` is a user-facing chat instruction.
- `loomcli ...` is the executable CLI command.
- `import loom` is the Python API.
- `loomcli ask` does not exist. Never run or suggest it.

## Lookup Workflow

When this skill applies:

1. Inspect `./loom` first.
2. Use `README.md`, `overview.md`, `*.card.md`, and `profile.json` only to locate the likely workspace and exact raw file.
3. Fetch only the exact raw file needed with `uv run loomcli get <workspace/path/to/file>` or `loom.get("workspace/path/to/file")`.
4. Read or parse the fetched local raw file.
5. Answer from the raw data, not from card summaries alone.
6. If no relevant Loom workspace or card exists, say that Loom does not currently contain the needed local data and continue with the best available approach.

## Raw File Access

Terminal form:

```bash
uv run loomcli get energy/technology-data/costs.csv
```

Python form:

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

`loom.get(...)` prefers local cache and fetches only the requested file.

## Answering Standard

- Cite the workspace and raw file path you used.
- State uncertainty when the raw file does not contain the requested value directly.
- Do not infer precise values from generated summaries when the raw CSV can be fetched.
