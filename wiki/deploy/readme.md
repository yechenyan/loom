# Loom Deploy

本文记录当前这套 Loom 在 Render 上的实际部署方式，以及后续发布时的操作。

## 当前线上地址

- Web: `https://loom-web.onrender.com`
- API: `https://loom-api-free.onrender.com`
- API health: `https://loom-api-free.onrender.com/health`
- Render Postgres: `loom-postgres`

## 当前线上资源

- Static Site: `loom-web`
- Web Service: `loom-api-free`
- Postgres: `loom-postgres`

说明：

- 现在的 API 服务名是 `loom-api-free`，不是最初蓝图里的 `loom-api`
- 原因是 Render free web service 不支持 persistent disk，所以最终线上用了一个新的 free API 服务，并把 `storage_root` 改到了 `/tmp/loom-server-storage`
- 这意味着 API 可以正常提供 HTTP 接口，但服务端文件存储不是持久化的，实例重启或重建后会丢

## 1. 从头部署

### 前提

需要先满足这些条件：

- 本地已经安装并登录 `render-cli`
- Render workspace 已经配置 billing
- GitHub 仓库可被 Render 拉取
- 当前代码已经推到要部署的分支，例如 `dev-1`

当前仓库实际部署使用的是：

- repo: `https://github.com/yechenyan/loom.git`
- branch: `dev-1`

### 第一步：创建 Postgres

先创建一个 free Postgres：

```bash
python - <<'PY'
from pathlib import Path
import json, urllib.request
import yaml

cfg = yaml.safe_load((Path.home()/'.render'/'cli.yaml').read_text())
key = cfg['api']['key']
owner = cfg['workspace']

payload = {
    "name": "loom-postgres",
    "ownerId": owner,
    "plan": "free",
    "region": "oregon",
    "version": "16",
    "enableDiskAutoscaling": False,
}

req = urllib.request.Request(
    "https://api.render.com/v1/postgres",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
PY
```

注意：

- free Postgres 不能自定义 `diskSizeGB`
- 需要等数据库状态变成 `available`
- 然后取它的 `internalConnectionString`

### 第二步：创建 API 服务

当前实际可用的 free 方案是：

```bash
render services create \
  --name loom-api-free \
  --type web_service \
  --repo https://github.com/yechenyan/loom.git \
  --branch dev-1 \
  --runtime python \
  --build-command 'pip install ./packages/loom-server' \
  --start-command 'loom-server run --storage-root /tmp/loom-server-storage --workspace-root /opt/render/project/src' \
  --health-check-path /health \
  --plan free \
  --region oregon \
  --env-var PYTHON_VERSION=3.12.8 \
  --env-var LOOM_SERVER_DATABASE_URL='postgresql+psycopg2://<user>:<password>@<internal-host>/<db>' \
  --env-var LOOM_SERVER_CORS_ORIGINS='*' \
  --output json \
  --confirm
```

说明：

- `LOOM_SERVER_DATABASE_URL` 要用 Postgres 的 internal connection string，并改成 `postgresql+psycopg2://...`
- `--workspace-root /opt/render/project/src` 是为了让服务端读取仓库里的 `test-project/loom/loom_explore`
- free web service 不支持 disk，所以这里必须用 `/tmp/loom-server-storage`

### 第三步：创建前端 Static Site

```bash
render services create \
  --name loom-web \
  --type static_site \
  --repo https://github.com/yechenyan/loom.git \
  --branch dev-1 \
  --build-command 'cd web && npm ci && npm run build' \
  --publish-directory web/dist \
  --env-var VITE_API_BASE_URL=https://loom-api-free.onrender.com \
  --output json \
  --confirm
```

### 第四步：验证上线

确认下面几个点：

- `https://loom-api-free.onrender.com/health` 返回 `{"ok":true}`
- `https://loom-api-free.onrender.com/api/workspaces` 返回 JSON
- `https://loom-api-free.onrender.com/api/explore/workspaces` 返回 JSON
- `https://loom-web.onrender.com` 可以打开

可直接用：

```bash
curl -fsS https://loom-api-free.onrender.com/health
curl -fsS https://loom-api-free.onrender.com/api/workspaces
curl -fsS https://loom-api-free.onrender.com/api/explore/workspaces
```

## 2. 后续发布部署

后续发布主要分两类。

### 2.1 只是代码更新

如果服务名、URL、数据库都不变，那么正常流程就是：

1. 本地改代码
2. 本地测试
3. 提交并 push 到 Render 绑定的分支，例如 `dev-1`
4. Render 自动 deploy

当前线上两个服务都开了 auto deploy，所以 push 到 `dev-1` 后会自动重建：

- `loom-api-free`
- `loom-web`

也可以手动触发：

```bash
render deploys create srv-d89ea6v7f7vs73c3vhgg --output json --confirm
render deploys create srv-d89e8j5ckfvc738hm5og --output json --confirm
```

其中：

- `srv-d89ea6v7f7vs73c3vhgg` 是 `loom-api-free`
- `srv-d89e8j5ckfvc738hm5og` 是 `loom-web`

### 2.2 前端只切 API 地址

如果只是 API 域名变了，不想改代码重提，也可以直接改 Render 上的环境变量：

```bash
python - <<'PY'
from pathlib import Path
import json, urllib.request
import yaml

cfg = yaml.safe_load((Path.home()/'.render'/'cli.yaml').read_text())
key = cfg['api']['key']

req = urllib.request.Request(
    "https://api.render.com/v1/services/srv-d89e8j5ckfvc738hm5og/env-vars/VITE_API_BASE_URL",
    data=json.dumps({"value": "https://loom-api-free.onrender.com"}).encode(),
    headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    method="PUT",
)

with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
PY
```

然后重发静态站：

```bash
render deploys create srv-d89e8j5ckfvc738hm5og --output json --confirm
```

### 2.3 需要改数据库或服务类型

如果需要：

- 把 API 从 free 升到支持 persistent disk 的 plan
- 改 Postgres plan
- 改 region
- 改服务名

这类变更建议按“重新建新资源 -> 验证 -> 切换前端地址 -> 删旧资源”的顺序做，不要直接在唯一线上服务上冒险。

## 3. 访问 URL

当前外部访问地址：

- Web 首页：`https://loom-web.onrender.com`
- API health：`https://loom-api-free.onrender.com/health`
- API workspaces：`https://loom-api-free.onrender.com/api/workspaces`
- API explore：`https://loom-api-free.onrender.com/api/explore/workspaces`

## 4. 发布 packages/loom

PyPI 项目名是 `loom-data`，源码版本号在仓库根目录的 `pyproject.toml`。

### 推荐发布脚本

仓库里现在提供了一个本地发布 CLI：

```bash
python scripts/release_pypi.py patch
```

这个脚本会按顺序执行：

1. 自动修改根目录 `pyproject.toml` 里的 `[project].version`
2. 对客户端发布相关代码跑 `ruff` lint
3. 跑最小发布回归测试
4. 清理旧的 `dist/` 和 `build/`
5. 重新 `uv build`
6. 调用 `uv publish`

支持的版本参数：

```bash
python scripts/release_pypi.py patch
python scripts/release_pypi.py minor
python scripts/release_pypi.py major
python scripts/release_pypi.py 0.1.5
```

常用附加参数：

```bash
python scripts/release_pypi.py patch --dry-run
python scripts/release_pypi.py patch --test-pypi
python scripts/release_pypi.py patch --skip-publish
```

如果 lint、测试、build 或 publish 任何一步失败，脚本默认会把 `pyproject.toml` 里的版本号自动改回去。只有显式传 `--keep-version-on-failure` 时，才会保留失败后的版本号变更。

如果想先只验证上传流程而不真正上传：

```bash
python scripts/release_pypi.py patch --dry-run
```

如果想先发到 TestPyPI：

```bash
python scripts/release_pypi.py patch --test-pypi
```

### PyPI 认证

`uv publish` 需要 PyPI 凭据。当前仓库没有内置发布凭据，所以发布机器上需要提前配置。

推荐把 gitignore 的私有发布配置单独放在：

```toml
config/local.toml
```

这个文件已经加入仓库根目录 `.gitignore`，不会被提交。

`config/release.toml` 不作为 secret 文件使用，后面如果要放可共享的发布配置，可以单独放在那里并正常提交。

建议内容：

```toml
[pypi]
token = "pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

发布脚本会按这个优先级找 token：

1. `UV_PUBLISH_TOKEN`
2. `PYPI_TOKEN`
3. `config/local.toml` 里的 `[pypi].token`

推荐直接用 PyPI API token：

```bash
export UV_PUBLISH_TOKEN=pypi-xxxx
python scripts/release_pypi.py patch
```

也可以显式传参：

```bash
PYPI_TOKEN=pypi-xxxx python scripts/release_pypi.py patch
```

如果未来改成 CI 发布，也可以接 PyPI Trusted Publishing；但在本地终端里直接运行 `uv publish` 时，默认不会自动拿到 OIDC token。

### 本次发布

这次发布准备的是：

- PyPI name: `loom-data`
- version: `0.1.1`

包含的关键变更：

- 默认 API base URL 改为 Render 线上地址 `https://loom-api-free.onrender.com`
- 新增 `loom set-api <url>`，可持久化切换 CLI 默认服务地址
- 保留 `LOOM_SERVER_URL` 和 Python `loom.set_base_url(...)` 覆盖能力

### 本次发布说明

本次为了发布客户端变更，版本已从：

- `0.1.0` -> `0.1.1`

这次版本包含：

- 默认 API base URL 改为 Render 线上地址
- 新增 CLI 命令 `loom set-api https://...`
- CLI / Python API 都支持持久化和覆盖 API 地址

## CLI 使用线上地址

### 推荐方式

CLI 推荐直接设环境变量：

```bash
export LOOM_SERVER_URL=https://loom-api-free.onrender.com
```

之后就可以直接用：

```bash
uv run python scripts/loom.py pull
uv run python scripts/loom.py pull-raw
uv run python scripts/loom.py push energy
```

也可以每次显式传：

```bash
uv run python scripts/loom.py pull --server-url https://loom-api-free.onrender.com
```

### 已验证结果

我已经实际验证过：

```bash
LOOM_SERVER_URL=https://loom-api-free.onrender.com uv run python scripts/loom.py pull
```

返回：

```text
No remote workspaces found to pull.
```

这说明：

- CLI 已经能走线上地址
- 线上 API 调用是通的
- 当前只是远端还没有 workspace 数据

Python API 侧也已验证：

```bash
LOOM_SERVER_URL=https://loom-api-free.onrender.com uv run python - <<'PY'
import loom
print(loom.get_base_url())
PY
```

输出：

```text
https://loom-api-free.onrender.com
```

## 当前限制

当前线上方案是“能跑的最低成本版本”，限制如下：

- `loom-api-free` 没有 persistent disk
- `/tmp/loom-server-storage` 不是持久化目录
- API 服务重建后，服务端文件存储会丢
- `api/explore/workspaces` 现在虽然可访问，但当前返回空列表，原因是部署代码里没有实际可展示的 `loom_explore` 内容

如果后续需要稳定可用，优先级最高的改进是：

1. 把 API 服务升级到支持 disk 的 Render plan
2. 把 `storage_root` 切到 persistent disk
3. 再补线上真实数据同步流程
