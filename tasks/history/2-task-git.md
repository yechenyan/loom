# Task: Loom Git And Sync

## Original Request

你可以看 tasks/history 了解前面做了哪些工作。

我现在想加一个新能力：
现在本地以及有了 `test-project/loom/loom_explore` 我想做一个变更记录的能力，
当刚运行完 `loom scan` 后，用户能看到有哪些文件变更，然后运行：

```bash
loom confirm
```

确认变更，类似在 git 中的提交。

服务器同步的功能，能把这个按照 workspace
也就是 `loom_explore` 下的第一级别文件夹，如 `energy`
和服务器进行同步。相当于用户在 codex chat 里输入：

```bash
loom push
```

会把里面的内容自动同步给服务器，类似在 git 中的 push。

如果输入：

```bash
loom pull
```

会自动更新服务器的版本，类似在 git 中的 pull。

## Completed Work

- Added a dedicated git repository inside `test-project/loom/loom_explore`.
- Updated install flow so `uv run python scripts/loom.py install` initializes the `loom_explore` git repo automatically.
- Updated scan flow so `loom scan <topic>` writes into the managed `loom_explore` repo and prints pending file changes immediately after scanning.
- Added `loom status` to show pending local changes and workspace sync metadata.
- Added `loom confirm` to commit local `loom_explore` changes into the dedicated git history.
- Added workspace snapshotting and local sync state tracking under `test-project/loom/loom_explore/.loom/state`.
- Implemented a FastAPI sync server backed by PostgreSQL for revision metadata and local server-side snapshot storage.
- Added `loom server-init-db` to create the local `loom` PostgreSQL database and initialize server tables.
- Added `loom server-run` to run the FastAPI sync server locally.
- Added `loom push` and `loom pull` for workspace-level synchronization against the server.
- Implemented the current simplified sync behavior:
  - `push` auto-confirms local pending changes, then overwrites the remote workspace head with a new revision.
  - `pull` overwrites the local workspace with the server snapshot, then auto-confirms the pulled state locally.
- Extended chat command parsing so `loom scan`, `loom status`, `loom confirm`, `loom push`, and `loom pull` can all route through the local fast path.
- Added a React web app under `web/` to browse `loom_explore` data from the browser.
- Added FastAPI read APIs for explore data so the web app can read workspace, dataset, and CSV profile summaries.
- Installed and started local PostgreSQL with Homebrew on this machine.
- Created and initialized the local PostgreSQL database:
  `postgresql+psycopg2://loom@127.0.0.1:5432/loom`
- Started the local FastAPI server at:
  `http://127.0.0.1:8765`
- Verified a real `loom push energy` end-to-end against the local FastAPI + PostgreSQL server.
- Added and updated tests covering install flow, scan/confirm workflow, sync server workflow, overwrite semantics, and explore API responses.

## Result

The task is complete.

Loom now supports:

- local git-style confirmation for `loom_explore`
- workspace-level push/pull against a local FastAPI + PostgreSQL sync server
- chat fast paths for scan/confirm/status/push/pull
- a local React web app for browsing the generated explore data

Key local endpoints and commands:

```text
FastAPI: http://127.0.0.1:8765
Web App: http://127.0.0.1:4173
```

```bash
python /Users/user/Documents/code2/loom/scripts/loom.py status energy
python /Users/user/Documents/code2/loom/scripts/loom.py confirm energy
python /Users/user/Documents/code2/loom/scripts/loom.py push energy
python /Users/user/Documents/code2/loom/scripts/loom.py pull energy
```
