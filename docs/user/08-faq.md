# FAQ

## Is `loom scan` a shell command?

No. `loom scan ...` is the chat form. The terminal command is `loomcli
scan-index ...`.

## Does `loomcli ask` exist?

No. Questions belong to the agent workflow. The agent should inspect `loom/`
first, then fetch exact raw files with `loomcli get` or `loom.get(...)`.

## Does `loom install` exist?

No. Install the package with a Python tool installer, then run `loomcli init`.

## Where should I put source data?

`raw_data/<workspace>` is the default convention, but Loom can scan any local
directory.

## What is a workspace?

A workspace is the named generated area under `loom/<workspace>`. It holds cards,
summaries, profiles, and manifests for one topic or project slice.

## What happens if I omit `to <workspace>`?

Loom reuses the recent workspace. If there is no recent workspace, it falls back
to `demo`.

## What files does Loom scan?

Inside each dataset root, Loom currently processes `loom.md` and `*.csv` files.
A directory becomes a dataset root when it contains `loom.md`.

## When should I run `confirm`?

Run `loomcli confirm <workspace>` after reviewing generated cards and summaries.
`confirm` records the reviewed workspace changes in the local Loom git history.

## Which document is authoritative?

`docs/reference/loom-reference.md` is the canonical behavior and terminology
reference.
