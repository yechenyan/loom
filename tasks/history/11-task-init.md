loom install 更新为 loom init。 

同时修改逻辑
1. 如果当前文件夹下有 loom 文件夹，显示选项：
   1. 提示用户需要手动删除才能重新 init
   2. 安装 skill
   3. 创建新工作区
   4. 帮助
2. 没有 loom 文件夹，则首先问：
  用户是用 openai/claude or copilot or claude ...
  用户选择后创建对应的 skill，而不是现在全都创建

3. 问用户默认工作区的名字：
  默认为当前用户的名字，查不到名字就 temo

4. 问是否教学。 如果选择是，则：
- 创建一个 example_raw 的文件夹, 与 loom 平行，里面放入  raw_example/cost
- 试试在 Agent 的对话中输入 
  - loom scan example_raw/cost 扫描数据，生成数据卡片
  - loom ask OCGT 的 capex 是多少 
  - loom push 上传数据，访问 https://loom-api-free.onrender.com 查看
- 安装完成，按回车退出

以上都用英语

## Implementation Summary

- Renamed the onboarding command from `loom install` to `loom init`, while keeping `install` as a compatibility alias.
- Switched the local workspace layout to `./loom` for generated cards and `./raw_data` for source data.
- Added interactive `init` behavior for both fresh setup and existing `loom/` directories, including single-agent skill installation, default workspace selection, and help/reset actions.
- Current code defaults the workspace name to `tempo` when the user accepts the default or enters an empty value.
- Embedded tutorial seed data directly in the package and updated the tutorial flow to use `loom scan raw_data/cost to cost`, `loom ask ...`, and `loom push`.
- Updated skill content, CLI parsing, routing, and docs so `loom ask <question>` and bare `loom <question>` now trigger a real local lookup flow instead of a placeholder message.
- Refreshed the root README, package README, manual, web examples, and tests to match the new command names and directory structure.
