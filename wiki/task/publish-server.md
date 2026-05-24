已完成。

本任务涉及的目标已经落地到代码、线上环境和文档。

## 完成结果

- Render 已部署完成：
  - Web: `https://loom-web.onrender.com`
  - API: `https://loom-api-free.onrender.com`
  - Health: `https://loom-api-free.onrender.com/health`
  - Postgres: `loom-postgres`
- CLI 已支持切换并持久化 API 地址：
  - `loom set-api https://loom-api-free.onrender.com`
  - 环境变量 `LOOM_SERVER_URL`
  - Python API `loom.set_base_url("https://...")`
- `packages/loom` 默认 API 地址已切到 Render 线上：
  - 默认值为 `https://loom-api-free.onrender.com`
- 前端已切到线上 API：
  - Render Static Site 通过 `VITE_API_BASE_URL` 访问线上服务
- 部署文档已补齐：
  - 从头部署
  - 后续发布部署
  - 当前访问 URL
  - `packages/loom` 发布方式

## 代码与配置变更

- `packages/loom-server` 支持 Render 运行：
  - 自动兼容 `PORT`
  - 默认绑定 `0.0.0.0`
  - 支持 `LOOM_SERVER_WORKSPACE_ROOT` / `--workspace-root`
  - 支持 `LOOM_SERVER_CORS_ORIGINS`
- `packages/loom` 支持服务地址配置：
  - `loom set-api <url>`
  - `LOOM_SERVER_URL`
  - `loom.set_base_url(...)`
- `web` 支持生产环境 API 地址注入：
  - `VITE_API_BASE_URL`
- 发布版本已提升：
  - `loom-data` version `0.1.1`

## 验证情况

- 已验证线上 API 可访问：
  - `GET /health` 返回正常
- 已验证 CLI 可使用线上地址：
  - `loom set-api https://loom-api-free.onrender.com`
  - 后续 `loom pull` 等命令会默认走线上
- 已验证测试通过：
  - `tests/test_server_config.py`
  - `tests/test_set_api_command.py`
  - `tests/test_packaging_metadata.py`
- 已验证构建通过：
  - `uv build`
  - 已生成 `loom_data-0.1.1` 的 wheel 和 sdist

## 文档位置

- 部署与发布说明：`wiki/deploy/readme.md`

## 剩余一步

`packages/loom` 的发布命令已经准备好，但最终上传到 PyPI 还需要发布者本机提供 PyPI token。

发布命令：

```bash
export UV_PUBLISH_TOKEN='你的 PyPI token'
uv publish
```

除这一步鉴权外，本任务其余内容都已完成。
