# loom-data

`loom-data` helps agents work with large local datasets without reading every raw CSV up front.

The workflow is:

1. Keep raw source data under `raw_data/<workspace>` or any directory that contains `loom.md`.
2. Scan that source into compact cards under `loom/<workspace>`.
3. Let the agent read `loom/` first.
4. Fetch only the exact raw files that are needed.

If you want better first-pass cards, put a short dataset description in `loom.md` and add a `Columns:` section with bullet points such as `- technology: ...`. Loom now carries those column notes into generated overviews and CSV cards.

## Naming

Loom now uses fixed names for each layer:

- `loom ...` is a chat instruction for the agent.
- `loomcli ...` is the execution command used by both humans and agents.
- `import loom` is the Python package import.

## Responsibility Map

```text
user
  -> chat: `loom ...`
     -> agent
        -> `loomcli ...`
           -> generate/update `loom/<workspace>`

user
  -> terminal: `loomcli ...`
     -> explicit local operation on Loom workspaces or raw cache
```

Recommended mental model:

- `loom`
  Ask the agent to do something in chat.
- `loomcli`
  Run an explicit terminal command yourself, or let the agent execute the underlying Loom action.

Example:

1. User says `loom scan raw_data/cost to cost` in chat.
2. The agent interprets that as a chat intent.
3. The agent runs `loomcli scan-index raw_data/cost to cost` internally.
4. Loom generates cards under `loom/cost`.
5. After review, a human or agent may run `loomcli confirm cost`.

## Install

Install `uv` first, then add the package:

```bash
uv add loom-data
```

Check the CLI:

```bash
uv run loomcli --help
```

## Initialize a project

Run this in the project root:

```bash
uv run loomcli init --agent codex
```

This is the recommended fast path for AI-assisted onboarding. When `--agent` is present, Loom skips the interactive setup, installs the selected agent skill, creates the default workspace from your local username, and installs the tutorial dataset automatically.

You can still use the interactive flow when you want to choose everything manually:

```bash
uv run loomcli init
```

This creates:

```text
loom/
  <workspace>/
  .loom/
raw_data/
  <workspace>/
```

`loomcli init` asks which assistant you use, which default workspace name you want, and whether to install the tutorial dataset.
`loomcli init --agent codex` skips those prompts and goes straight to the tutorial-ready setup.

## Chat workflow

These are chat messages for your agent, not shell commands:

```text
loom scan raw_data/energy to energy
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
```

Expected behavior:

1. `loom scan ...`
   The agent runs `loomcli scan-index ...` to generate the first pass of cards, then continues refining the cards in chat. A complete scan review should read each dataset `loom.md`, check the generated `overview.md` and cards, make sure the dataset purpose and each column meaning are explained clearly, and only then suggest `loomcli confirm`.
2. `loom ask ...` or `loom <问题>`
   The agent inspects `loom/` first, then uses `loomcli get` only if it needs a specific raw file.

If the request is data-related but does not mention Loom explicitly, the installed skill should still make the agent think of Loom first.

## Terminal workflow

Use explicit terminal commands when you want to operate Loom by hand:

```bash
uv run loomcli scan-index raw_data/energy to energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli get energy/technology-data/costs.csv
uv run loomcli set-api https://loom-api-free.onrender.com
```

Notes:

- `loomcli scan-index` is the explicit scan command. Agents can also use it as the execution step behind chat `loom scan ...`.
- `loomcli scan` is not used; use chat `loom scan ...` or `loomcli scan-index ...` instead.
- `loomcli ask` does not exist anymore. Questions belong to the agent's Loom-first lookup workflow.
- After `loomcli init --agent ...`, the agent should tell the user that `loom ...` belongs in chat and `uv run loomcli ...` belongs in the terminal.
- If you omit `to <workspace>` in a scan request, Loom reuses the most recent workspace or falls back to `temporary`.

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` reuses local cache when possible and only downloads the latest raw file when needed.

## Workspace rules

- One workspace can track multiple source directories.
- Dataset paths inside one workspace must stay unique.
- Scan state is incremental per workspace and per source path.
- Generated cards and manifests store source-relative raw paths, so moving the project does not force a rebuild of unchanged datasets.

## Web app

Explore data online at [https://loom-web.onrender.com](https://loom-web.onrender.com).

## Maintainers

This repo also includes workspace skills for maintainer workflows:

- `.agents/skills/loom-cli-release` publishes new `loom-data` PyPI releases.
- `.agents/skills/loom-render-deploy` deploys the current pushed commit to the Render API and web services.
