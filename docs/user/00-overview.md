# User Guide Overview

Loom helps an agent work with local datasets without reading every raw file up
front. It builds a small searchable workspace under `loom/`, keeps raw data
under `raw_data/` or another local source directory, and lets the agent fetch
only the exact raw files needed to answer a question.

For the exact behavior contract, see `docs/reference/loom-reference.md`.

## Reading Order

1. `00-overview.md`: what Loom is and which guide to read next.
2. `01-quickstart.md`: install, initialize, scan the tutorial data, and ask a
   first question.
3. `02-workspaces.md`: how `loom/`, `raw_data/`, workspaces, datasets, and raw
   caches fit together.
4. `03-scan-and-review.md`: how to turn source data into Loom cards.
5. `04-ask-and-fetch.md`: how agents answer data questions from cards and exact
   raw files.
6. `05-sync-and-raw-cache.md`: how to confirm, push, pull, and materialize raw
   files.
7. `06-python-api.md`: how to use `import loom` from Python.
8. `07-command-reference.md`: supported chat forms, CLI commands, and Python
   calls.
9. `08-faq.md`: common command and workflow questions.

## Three Ways to Use Loom

- Chat: write `loom ...` instructions to an agent. The agent interprets the
  request and may run `loomcli`.
- Terminal: run `loomcli ...` commands yourself for explicit local operations.
- Python: call `import loom` when code needs a local path to a raw file.

Keep the names separate: `loom-data` is the package, `loomcli` is the command,
`loom ...` is chat language, and `import loom` is the Python API.
