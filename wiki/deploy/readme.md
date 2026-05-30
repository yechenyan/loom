# Loom Deploy

本文只记录当前仓库里 `web` 和 `server` 的部署方式。

先说明两个事实：

- 前端目录是 `web/`
- 后端不是顶层 `server/`，而是 `packages/loom-server/`

当前部署的代码真相以 [render.yaml](/Users/maxiao/Documents/code2/loom/render.yaml) 为准，文档只是解释它。

## 当前部署对象

- `loom-api-free`
  Render Web Service，运行 `packages/loom-server`
- `loom-web`
  Render Static Site，构建 `web`
- `loom-postgres`
  Render Postgres，给 `loom-server` 使用

## 当前 Render 配置

`render.yaml` 里现在定义的是：

- API service
  - type: `web`
  - runtime: `python`
  - name: `loom-api-free`
  - plan: `starter`
  - build command: `pip install ./packages/loom-server`
  - start command: `loom-server run --storage-root /var/data/loom-server-storage --workspace-root /opt/render/project/src`
  - health check: `/health`
  - disk mount: `/var/data`
- Web service
  - type: `web`
  - runtime: `static`
  - name: `loom-web`
  - build command: `cd web && npm ci && npm run build`
  - publish path: `./web/dist`
  - env: `VITE_API_BASE_URL=https://loom-api-free.onrender.com`
  - SPA rewrite: `/* -> /index.html`
- Database
  - name: `loom-postgres`
  - plan: `free`

说明：

- 虽然服务名还是 `loom-api-free`，但当前蓝图里它跑的是 `starter` plan，不是 free web service
- 当前 API 依赖 persistent disk，所以 `render.yaml` 使用了 `/var/data/loom-server-storage`
- 如果你把 API 改回 free web service，就不能继续用 disk，必须改成 `/tmp/...`，并接受重启后数据丢失

## 推荐部署方式

推荐直接用 Render Blueprint 部署整个仓库，不要分别在 Dashboard 里手工点三套资源。

好处：

- `web`、`server`、`postgres` 一次建好
- 环境变量和磁盘挂载不会漏
- 后续配置改动直接以 `render.yaml` 为准

## 一次性从头部署

### 1. 准备条件

- 代码已经推到 GitHub
- Render 可以访问这个仓库
- Render workspace 已开通可用套餐
- 本地如果要先校验蓝图，已经安装并登录 `render-cli`

### 2. 校验 Blueprint

如果本地装了 `render-cli`，先在仓库根目录执行：

```bash
render blueprint validate
```

如果这里报错，先修 `render.yaml`，不要带着错误去 Dashboard 创建资源。

### 3. 在 Render 创建 Blueprint

在 Render Dashboard 中：

1. New +
2. Blueprint
3. 选择这个 GitHub 仓库
4. 选择包含当前 `render.yaml` 的分支
5. Review 后点击 Apply

Render 会按 `render.yaml` 创建：

- `loom-postgres`
- `loom-api-free`
- `loom-web`

### 4. 首次部署后检查环境变量

重点确认 API 服务上这几个值：

- `PYTHON_VERSION=3.12.8`
- `LOOM_SERVER_DATABASE_URL`
  来自 `loom-postgres.connectionString`
- `LOOM_SERVER_CORS_ORIGINS=*`

重点确认前端服务上这个值：

- `VITE_API_BASE_URL=https://loom-api-free.onrender.com`

如果你改了 API 域名，前端这里也必须一起改。

### 5. 验证服务

部署完成后至少检查这几个地址：

```bash
curl -fsS https://loom-api-free.onrender.com/health
curl -fsS https://loom-api-free.onrender.com/api/workspaces
curl -fsS https://loom-api-free.onrender.com/api/explore/workspaces
```

期望结果：

- `/health` 返回 `{\"ok\":true}`
- 另外两个接口返回合法 JSON
- `https://loom-web.onrender.com` 能正常打开，并且能请求 API

## 手工部署顺序

如果你暂时不用 Blueprint，手工部署顺序必须是：

1. 先建 Postgres
2. 再建 API service
3. 最后建 web static site

原因是前两者互相依赖：

- API 要先拿到数据库连接串
- Web 要先拿到 API 地址

## 手工部署 API

后端实际启动入口来自 `packages/loom-server` 的 `loom-server` CLI。

对应命令可以概括成：

```bash
pip install ./packages/loom-server
loom-server run --storage-root /var/data/loom-server-storage --workspace-root /opt/render/project/src
```

Render 里需要补齐这些配置：

- service type: `Web Service`
- runtime: `Python`
- build command: `pip install ./packages/loom-server`
- start command: `loom-server run --storage-root /var/data/loom-server-storage --workspace-root /opt/render/project/src`
- health check path: `/health`
- disk mount path: `/var/data`
- env:
  - `PYTHON_VERSION=3.12.8`
  - `LOOM_SERVER_DATABASE_URL=<postgres connection string>`
  - `LOOM_SERVER_CORS_ORIGINS=*`

关于 `workspace-root`：

- 这里应该指向 Render checkout 后的仓库根目录
- 对当前 Render Python 服务，仓库根目录就是 `/opt/render/project/src`
- 如果服务端需要读取仓库里的 `loom/` 内容，这个参数不能漏

## 手工部署 Web

前端是标准 Vite 静态站点，部署要求比 API 简单。

Render 里需要填写：

- service type: `Static Site`
- build command: `cd web && npm ci && npm run build`
- publish directory: `web/dist`
- env:
  - `VITE_API_BASE_URL=https://loom-api-free.onrender.com`

如果 API 域名不是上面这个值，就把它替换成你的实际 server URL。

## 后续更新部署

如果只是代码更新，没有改服务名、数据库或域名，正常流程就是：

1. 本地提交代码
2. push 到 Render 绑定分支
3. 等 Render 自动重新部署

如果用的是 Blueprint，优先继续维护 [render.yaml](/Users/maxiao/Documents/code2/loom/render.yaml)，不要只在 Dashboard 里手改。

## 脚本化发布

仓库里现在提供了统一脚本：

```bash
uv run python scripts/deploy_render.py
```

默认行为：

- 检查当前 worktree 是否干净
- 检查 `HEAD` 是否已经 push 到 `origin/<current-branch>`
- 执行 `render blueprints validate`
- 读取 Render 服务列表并找到：
  - `loom-api-free`
  - `loom-web`
- 触发两个服务的 deploy，并等待它们变成 `live`
- 验证：
  - `https://loom-api-free.onrender.com/health`
  - `https://loom-web.onrender.com`

常用变体：

```bash
uv run python scripts/deploy_render.py --api-only
uv run python scripts/deploy_render.py --web-only
uv run python scripts/deploy_render.py --skip-validate
uv run python scripts/deploy_render.py --commit <sha>
```

如果你只是要把当前已 push 的改动上线，优先用这个脚本，不要手工敲一串 `render deploys create ...`。

## 变更 API 地址时要一起改的地方

如果你换了 API 域名，不要只改 Render 服务本身，还要一起检查这些位置：

- `render.yaml` 里的 `VITE_API_BASE_URL`
- `packages/loom/src/loom/server_config.py` 里的默认 CLI 地址
- `README.md` 和 `wiki/manule/readme.md` 里示例用到的线上地址

否则会出现：

- Web 还在请求旧 API
- CLI 默认还指向旧地址
- 文档继续教用户连旧服务

## 常见问题

### 1. Web 打得开，但数据加载失败

优先检查：

- `VITE_API_BASE_URL` 是否指向正确 API
- API 的 CORS 是否包含前端来源
- API 的 `/health` 是否正常

当前代码里 `LOOM_SERVER_CORS_ORIGINS` 默认可设为 `*`，这是最省事的部署方式。

### 2. API 启动成功，但数据会丢

这通常是因为：

- 你没有挂 persistent disk
- 或者把 `storage-root` 配到了 `/tmp`

当前 `render.yaml` 选择 `starter + disk`，就是为了避免这个问题。

### 3. Web 本地开发能通，线上不通

本地开发时 `web/vite.config.js` 会把 `/api` 代理到：

```text
http://127.0.0.1:8765
```

但线上静态站没有这个代理，所以线上必须显式配置：

```text
VITE_API_BASE_URL=https://你的-api-域名
```
