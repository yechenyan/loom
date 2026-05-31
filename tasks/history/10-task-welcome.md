# Task: Welcome Page Refresh

## Original Request

修改 web 里对项目介绍的宣传页：

修改最上面的 get start 部分：
1. 安装：
有个选项卡，对应 ChatGPT/claude/curse ,
请复制下面的话，聊天中粘贴给 AI Agent
<你编一句话， 安装 uv， 安装 loom-data， 运行 loom-data init，请参考最新的 loom init 方法写, 确保这句话贴给 AI Agent 后， 能自动完成 loom 的安装>

2. 扫描 + 创建数据卡片
在聊天中粘贴给 AI Agent
loom scan <path>
如: loom scan raw_data/cost

3. 寻问问题
loom ask <question>
如： loom ask OCGT 的成本是多少
AI 在写代码/文章时也可自行查询数据


上面的的最好能放到 AI chat 中，让用户干能看出是在和 AI 对话，不用操作代码，自然
页面要好看

## Completed Work

- Reworked the top section of [web/src/App.jsx](/Users/user/Documents/code2/loom/web/src/App.jsx) into a Chinese AI-chat-style onboarding flow.
- Added agent tabs for `ChatGPT`, `Claude`, and `Cursor`, each with a tailored installation prompt based on the current `uv add loom-data` + `uv run loom init` workflow.
- Added a copy button so users can copy the install prompt directly into their AI chat tool.
- Replaced the previous command-heavy demo cards with three onboarding cards:
  - install Loom through AI chat
  - scan a folder with `loom scan raw_data/cost`
  - ask questions with `loom ask OCGT 的成本是多少`
- Updated the visual flow so the last step now highlights `loom ask` instead of `loom get`.
- Refreshed [web/src/styles.css](/Users/user/Documents/code2/loom/web/src/styles.css) to support the new chat UI, tabs, copy action, and polished onboarding layout.
- Updated [README.md](/Users/user/Documents/code2/loom/README.md) and [docs/reference/loom-reference.md](/Users/user/Documents/code2/loom/docs/reference/loom-reference.md) so the docs match the new AI-assisted install and onboarding flow.

## Result

The welcome page now presents Loom as an AI-first onboarding experience: users can copy a natural-language install prompt, ask the agent to scan data, and then continue with `loom ask` directly in chat.
