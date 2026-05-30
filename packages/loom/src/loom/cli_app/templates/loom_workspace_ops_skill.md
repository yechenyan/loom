---
name: loom-workspace-ops
description: Use for Loom setup and operational commands: initializing Loom, installing agent skills, checking status, confirming, pushing, pulling, pulling raw files, setting the API server, or explaining chat-vs-CLI usage.
---

# loom-workspace-ops

Loom helps agents use project-local datasets: inspect lightweight cards in `./loom` first, fetch exact raw files only when needed, and answer source-backed data questions from raw data.

## Use This Skill

Use this skill for Loom operations:

- Initialize a project with Loom.
- Install Loom agent skills.
- Check workspace status.
- Confirm generated cards after review.
- Push or pull Loom workspaces.
- Pull raw files.
- Set the Loom API server.
- Explain the difference between chat instructions and terminal commands.

Do not use this skill to:

- Answer data questions. Use `loom-local-data-lookup`.
- Scan and review datasets. Use `loom-dataset-scan-review`.
- Treat unsupported chat forms as valid commands.

## Names

- `loom ...` is a user-facing chat instruction.
- `loomcli ...` is the executable CLI command.
- `import loom` is the Python API.
- `loom-data` is the published package name.

Do not mix these layers.

## Setup

Recommended fast path:

```bash
uv add loom-data
uv run loomcli init --agent <agent>
```

Supported agent values:

- `codex`
- `claude`
- `cursor`
- `copilot`

Use the agent value that matches the current assistant. For example, Codex should use `codex`, Claude should use `claude`, Cursor should use `cursor`, and Copilot should use `copilot`.

`loomcli init --agent ...` skips interactive setup, installs Loom agent skills, creates `./loom` and `./raw_data`, creates a default workspace, and installs tutorial data.

## Operations

Use these terminal commands for explicit operations:

```bash
uv run loomcli status energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli set-api https://loom-api-free.onrender.com
```

Chat intents such as `loom status energy`, `loom confirm energy`, `loom push energy`, and `loom pull energy` may be interpreted as instructions to run the matching `loomcli` command.

Unsupported chat forms:

- `loom init`
- `loom get`
- `loom set-api`
- `loom install`

Unsupported CLI forms:

- `loomcli ask`
- `loomcli install`
