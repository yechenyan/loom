# Chat vs CLI

Loom uses different names for chat and execution. Keep them separate.

## Chat

Use `loom ...` in an agent conversation:

```text
loom scan raw_data/cost to cost
loom ask "What is the capex for OCGT?"
loom push cost
```

Meaning:

- the user is asking the agent to do something
- the agent decides whether to run `loomcli`

## CLI

Use `loomcli ...` in the terminal:

```bash
uv run loomcli scan-index raw_data/cost to cost
uv run loomcli confirm cost
uv run loomcli push cost
```

Meaning:

- a human or agent is executing an explicit command

## Rules

- Do not run `loom ...` lines in the shell.
- Do not document `loomcli ask`; it does not exist.
- When in doubt, check `docs/reference/loom-reference.md`.
