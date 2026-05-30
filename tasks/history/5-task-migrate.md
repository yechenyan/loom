# Task: Explore Sync Rebase And Raw Conflict Handling

## Original Request

先看下 tasks/history 的逻辑。 

当前 pull 和 push 时是直接覆盖。

调整成：
对于 explore:
push 前先自动 pull 下，
如同 git 一样进行 migrate，用 rebase
如果没冲突，合并完后自动 confirm ，然后自动push

如果有冲突，由 AI 自行处理冲突， 并提示用户由冲突
用户之后需要运行 loom confirm 确认对冲突的解决。 之后用户再 运行 loom push 同步。

对于 ./loom/raw
pull 完后（如果有冲突则等 confirm 后） 根据最新的结果更新 .loom 里的
如果线上本地一致则不用做任何处理

对于 test-project/loom/loom_raw 里的文件，如果有冲突不要替换，只在 loom.md 旁新建一个 xxx.md（名字你定）  记录这个已经和服务端的不一致了，并提醒用户。 

补充要求：

- `pull` 的时候不需要所有的 raw 都下载下来更新，只需要更新 `./loom/raw` 里有的文件即可

## Completed Work

- Reworked `loom pull` and `loom push` from overwrite semantics to a rebase-style sync flow for `loom_explore`.
- Added local merge/replay support for one workspace at a time:
  - base snapshot reconstruction from the last synced commit
  - three-way merge between base, local, and remote workspace snapshots
  - conflict marker generation when local and remote edits overlap
- Updated `push` flow so it now:
  - auto-confirms pending local workspace changes
  - checks the remote head revision first
  - auto-runs the same rebase path as `pull` when the remote is ahead
  - auto-confirms the rebased result when there is no conflict
  - continues with incremental push after the rebase succeeds
- Updated `pull` flow so it now:
  - fast-forwards when there are no local confirmed commits after the sync base
  - rebases local confirmed commits onto the latest remote revision when needed
  - stops on conflict without auto-confirming
- Extended workspace sync state with pending rebase metadata so conflict resolution can continue safely on the next `confirm` / `push`.
- Updated CLI output and exit codes:
  - `pull` / `push` now return non-zero on rebase conflict
  - users are told to resolve conflicts, run `loom confirm <workspace>`, then `loom push <workspace>`
  - `status` now shows `Pending rebase revision` when a workspace is mid-resolution
- Changed automatic raw refresh after `loom pull` / `loom push`:
  - it now refreshes only files already present in `test-project/loom/.loom/raw/<workspace>/...`
  - it no longer downloads every raw file from the remote manifest during normal workspace sync
- Kept explicit raw sync behavior for `loom.pull(...)` and `loom pull-raw ...` so those commands can still refresh a full raw workspace cache intentionally.
- Added local raw conflict detection for `test-project/loom/loom_raw/<workspace>/...`:
  - Loom never overwrites local raw source files
  - when a local raw file and the remote raw manifest disagree, Loom writes `loom.raw-conflict.md` next to the nearest `loom.md`
  - CLI output includes the generated conflict notice path
- Added and updated tests covering:
  - push auto-rebase success
  - push conflict, manual resolve, confirm, and retry push
  - pull rebase success when local confirmed commits exist
  - pull conflict when local confirmed commits exist
  - raw cache refresh limited to already cached files during normal pull
  - raw conflict notice generation

## Result

The migrate task is complete.

Verified behavior:

- `loom push` now behaves like “auto-confirm, rebase if needed, then push”
- `loom pull` no longer blindly overwrites local confirmed work
- rebase conflicts pause the sync and preserve conflict markers for manual resolution
- normal workspace sync only refreshes existing `.loom/raw` cache entries
- local `loom_raw` source files are never replaced automatically
- raw source conflicts generate `loom.raw-conflict.md` notices for the user

Verification run:

```bash
pytest -q
```

Result:

```text
30 passed
```
