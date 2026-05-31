# Architecture

This is a lightweight map of the current repository structure.

## Main Packages

- `packages/loom/src/loom/`
  Client package, chat parsing, scan logic, sync logic, and CLI wiring.
- `packages/loom-server/src/loom_server/`
  Server runtime and service implementation.

## Key Entry Points

- `packages/loom/src/loom/cli_app/parser.py`
  Defines the public CLI commands.
- `packages/loom/src/loom/chat.py`
  Defines the supported chat forms and parsing behavior.
- `packages/loom/src/loom/cli_app/init_flow.py`
  Defines `loomcli init` behavior.
- `scripts/loomcli.py`
  Repository-local launcher for the CLI.

## Documentation Contract

- Code is the source of truth.
- `docs/reference/loom-reference.md` is the canonical written summary of current behavior.
- User and developer guides should derive from the reference instead of redefining behavior.
