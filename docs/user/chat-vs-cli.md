# Chat vs CLI

Loom uses different names for chat and execution. Keep them separate.

## Chat

Use `loom ...` in an agent conversation:

```text
loom scan raw_data/demo_germany_energy_data to germany_energy
loom ask "What German wind and solar data is available?"
loom push germany_energy
```

Meaning:

- the user is asking the agent to do something
- the agent decides whether to run `loomcli`

## CLI

Use `loomcli ...` in the terminal:

```bash
uv run loomcli scan-index raw_data/demo_germany_energy_data to germany_energy
uv run loomcli confirm germany_energy
uv run loomcli push germany_energy
```

Meaning:

- a human or agent is executing an explicit command

## Rules

- Do not run `loom ...` lines in the shell.
- Do not document `loomcli ask`; it does not exist.
- When in doubt, check `docs/reference/loom-reference.md`.
