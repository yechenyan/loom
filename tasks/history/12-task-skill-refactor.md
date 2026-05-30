# Task: Loom Agent Skill Refactor

## Original Request

用户要求先研究 Loom 文档和代码，重点重构安装到其他项目里的 Loom skill。

关键要求：

- `loom scan ...` 后 agent 必须进入 review，而不是扫描完就结束。
- `loom ask ...` 是硬触发，必须查 Loom。
- 不加 `loom` 时，如果用户在建模、写代码、写文档、写论文时需要项目本地数据事实，agent 也应优先从 Loom 查。
- 旧 `loom-data` skill 可以完全重构，不需要兼容旧项目或旧写法。
- Skill 必须用英语，并满足 skill 格式。

## Implementation Summary

- Removed the old single `loom-data` installed skill.
- Added three focused English skills:
  - `loom-local-data-lookup`
  - `loom-dataset-scan-review`
  - `loom-workspace-ops`
- Updated skill installation so `loomcli init --agent ...` installs the three focused skills for the selected agent.
- Tightened lookup guidance so `loom ask ...` and bare `loom <question>` are hard lookup triggers, while non-explicit Loom use is limited to project-local, source-backed data facts.
- Tightened scan guidance so `loom scan ...` is treated as chat intent, translated to `loomcli scan-index ...`, and followed by required review and card curation before suggesting confirm.
- Updated init/help wording, reference docs, user quickstart, package README, and tests for the new skill split.
- Added regression tests to ensure old broad data-trigger wording and the old `loom_data_skill.md` template do not return.

## Verification

- `UV_CACHE_DIR=.uv-cache uv run python -m unittest tests/test_skill_markdown.py tests/test_install.py`
- `UV_CACHE_DIR=.uv-cache uv run python -m unittest tests/test_chat.py tests/test_cli_workflow.py tests/test_scanner.py tests/test_skill_markdown.py tests/test_install.py`

Full unittest discovery still requires missing optional test dependencies such as `httpx` and `pytest` in the current environment.
