# Sync and Raw Cache

Loom keeps generated workspace files and raw files separate. Workspace sync
moves generated cards and manifests. Raw sync materializes raw files into the
local cache.

## Check Local Changes

```bash
loomcli status energy
```

Without a workspace, `status` shows pending changes across all workspaces:

```bash
loomcli status
```

## Confirm Reviewed Changes

```bash
loomcli confirm energy
```

`confirm` saves pending generated workspace changes into the local Loom git
history. Use it after reviewing scan output.

You can add a message:

```bash
loomcli confirm energy --message "Review energy dataset cards"
```

## Push and Pull Workspaces

Push reviewed workspace files to the configured Loom API server:

```bash
loomcli push energy
```

Pull workspace files from the server:

```bash
loomcli pull energy
```

Without a workspace, `push` uses local workspaces and `pull` uses remote
workspaces.

To change the default server:

```bash
loomcli set-api https://loom-api-free.onrender.com
```

You can also pass a server URL on commands that support it:

```bash
loomcli push energy --server-url https://example.com
loomcli pull energy --server-url https://example.com
```

## Pull Raw Files

Pull raw files for a workspace into `loom/.loom/raw/<workspace>`:

```bash
loomcli pull-raw energy
```

Without a workspace, `pull-raw` pulls raw files for remote workspaces. Raw files
may be downloaded from the server or linked from local source data when Loom can
find the matching local file.

## Chat Forms

These chat instructions may be interpreted by an agent as matching CLI actions:

```text
loom status energy
loom confirm energy
loom push energy
loom pull energy
```

Use terminal commands when you want to execute the operation yourself.
