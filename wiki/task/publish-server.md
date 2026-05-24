已完成。

交付内容：

- 新增 [render.yaml](/Users/maxiao/Documents/code2/loom/render.yaml)，用 Render 默认域名部署三项资源：
  - `loom-api`：Python Web Service，`plan: free`
  - `loom-web`：Static Site，直接发布 `web/dist`
  - `loom-postgres`：Render Postgres，`plan: free`
- `packages/loom-server` 现在支持 Render 所需配置：
  - 自动兼容 `PORT`
  - 在 Render 默认改绑 `0.0.0.0`
  - `LOOM_SERVER_WORKSPACE_ROOT` / `--workspace-root`
  - `LOOM_SERVER_CORS_ORIGINS`
- `packages/loom` 现在支持改 base URL：
  - Python API: `loom.set_base_url("https://...")`
  - 环境变量: `LOOM_SERVER_URL`
  - CLI: `--server-url`
- `web` 现在支持：
  - 本地继续走 Vite proxy
  - Render 静态部署时通过 `VITE_API_BASE_URL` 连接服务端

本地模式：

```bash
uv run python scripts/loom-server.py run --storage-root .loom-server-storage
cd web && pnpm dev --host 127.0.0.1
```

Render 模式：

1. 把仓库连到 Render
2. 用仓库根目录的 `render.yaml` 创建 Blueprint
3. 首次部署后确认 API 域名是否为 `https://loom-api.onrender.com`
4. 如果 Render 分配的默认域名不同，更新静态站点的 `VITE_API_BASE_URL`

关于最便宜部署：

- `web` 用 Static Site 最省，Render 官方文档说明静态站点可免费部署，适合直接发 `dist`
- `loom-api` 用 free Web Service
- `postgres` 用 free Render Postgres

注意：

- Render 官方文档当前说明 free Postgres 会在创建 30 天后过期，而且每个 workspace 只能有一个 active free Postgres
- 如果后面需要长期稳定使用，最先建议升级的是 Postgres

