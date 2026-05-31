# Command Reference

This page is a user-facing index of the supported chat forms, terminal commands,
and Python calls. For the canonical contract, see
`docs/reference/loom-reference.md`.

## Chat Forms

Use these in an agent conversation:

```text
loom scan <path> [to <workspace>]
scan <path> with loom
loom ask <question>
loom <question>
loom status [workspace]
loom confirm [workspace]
loom push [workspace]
loom pull [workspace]
```

Do not type these chat forms into a shell.

## Terminal Commands

Use these in a terminal:

```bash
loomcli init
loomcli init --agent codex
loomcli init --agent codex --no-tutorial
loomcli scan-index <path> [to <workspace>]
loomcli status [workspace]
loomcli confirm [workspace]
loomcli push [workspace]
loomcli pull [workspace]
loomcli pull-raw [workspace]
loomcli get <workspace/path/to/file>
loomcli set-api <base-url>
```

Useful options:

- `--workspace-root <path>`: run against a project root other than the current
  directory.
- `--no-tutorial`, `--tutorial-url`, `--tutorial-sha256`, `--force-tutorial`:
  control tutorial dataset download during `init`; custom tutorial URLs require
  a matching `--tutorial-sha256`.
- `--message <text>`: add a message to `confirm` or `push`.
- `--server-url <url>`: override the server for `get`, `push`, `pull`, or
  `pull-raw` when supported.

## Server Commands

These are for running a Loom sync server, not for normal data lookup:

```bash
loomcli server-init-db
loomcli server-run
```

`server-init-db` accepts database, storage-root, and workspace-root options.
`server-run` also accepts host and port options. Most users only need the hosted
or configured server used by `push`, `pull`, and `get`.

## Python Calls

```python
import loom

path = loom.get("workspace/path/to/file.csv")
results = loom.pull("workspace")
```

`loom.get(...)` is the normal Python entry point for analysis because it
materializes only the exact raw file requested.

## Unsupported Forms

These are not supported:

```text
loom install ...
loomcli install ...
loomcli ask ...
loom get ...
loom init ...
loom set-api ...
```

Use the matching supported chat or terminal form instead.
