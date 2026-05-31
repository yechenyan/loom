原来的 loom scan 是扫描固定的文件夹即 raw，现在改了：

loom scan <path> to <workspace>

path: 要扫描的文件夹，支持相对路径和觉得路径
workspace: 在哪个 workspace 建 datacard

to <workspace> 是可省项目

loom scan <path> to <workspace> 是可以在 chat 聊天中运行的

要求做的工作：
1. 修改测试
2. 改 CLI
3. 确保流程能跑通
4. 改文档
5. 改 html 的说明

你有问题么？

---

完成总结：

- `loom scan` 已切换为新语法 `loom scan <path> [to <workspace>]`，并支持在聊天路由里直接运行。
- `path` 现在是必填项；省略 `to <workspace>` 时会复用最近一次 scan/创建的 workspace，没有历史时自动使用 `temporary`。
- CLI、chat 解析、扫描状态记录和最近 workspace 记忆逻辑都已更新。
- 测试已同步到新语法，并补充了省略 workspace、自动使用 `temporary`、缺少 path 报错等场景。
- README、`docs/reference/loom-reference.md`、workspace skill 文档和 web 页面说明都已同步到新行为。
- 对外公开的 Python API 已收口为 `scan_path_to_explore`，不再导出旧的 `scan_topic_to_explore`。
