# Scan and Review

Scanning turns local source data into Loom cards that an agent can inspect
before reading raw files.

## Chat Scan

Use this form in agent chat:

```text
loom scan raw_data/energy to energy
/loom-scan raw_data/energy to energy
```

The `to <workspace>` part is optional:

```text
loom scan raw_data/energy
/loom-scan raw_data/energy
scan raw_data/energy with loom
```

When no workspace is given, Loom uses the recent workspace or `demo`.

## Terminal Scan

Use this form in the terminal:

```bash
loomcli scan-index raw_data/energy to energy
```

`scan-index` requires a source path. It accepts the same optional `to
<workspace>` suffix.

## What the Scan Reads

For each dataset root, Loom currently reads:

- `loom.md`
- `*.csv`

Use `loom.md` to explain the dataset's purpose, provenance, column meanings,
units, caveats, and recommended use. Better `loom.md` files produce better
first-pass summaries.

## What the Scan Writes

The scan writes generated files under `loom/<workspace>/` and scan state under
`loom/.loom/state/`. It creates dataset overviews, CSV cards, JSON profiles, and
`scan-manifest.json`.

Rescans reuse unchanged CSV hashes and profiles, then rebuild only changed
datasets. If a previously scanned source dataset is missing, Loom keeps the
existing generated files and reports the missing source dataset.

## Review Before Confirming

Treat the first scan output as a draft. A good agent workflow is:

1. Run `loomcli scan-index ...`.
2. Review generated `overview.md` and `.card.md` files.
3. Read each source `loom.md`.
4. Fix generic or incomplete generated summaries.
5. Run `loomcli status <workspace>`.
6. Run `loomcli confirm <workspace>` only after the cards are ready.

This review step matters because future questions depend on the generated cards
to find the right raw file quickly.
