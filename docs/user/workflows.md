# User Workflows

For the exact behavior contract, see `docs/reference/loom-reference.md`.

## Scan a Dataset

1. Put source data in `raw_data/<workspace>` or another local directory.
2. Add `loom.md` when you want better first-pass summaries.
3. Ask the agent:

```text
loom scan raw_data/energy to energy
```

4. The agent should run `loomcli scan-index ...`, then review the generated cards before calling the scan ready.

## Ask a Data Question

1. Ask in chat:

```text
loom ask OCGT 的成本是多少
```

2. The agent should inspect `loom/` first.
3. The agent should fetch only the exact raw file needed.
4. The answer should come from the fetched local data, not from a guessed summary.

## Confirm and Sync

Use terminal commands when you want explicit local operations:

```bash
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
```
