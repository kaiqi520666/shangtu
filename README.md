# Shangtu（商图）

AI 驱动的电商商品图批量生成 SaaS。上传商品图 + 选平台/尺寸 + AI 自动分析卖点，生成多种用途素材（主图、套图、详情图、服饰穿搭）。

- 后端：Python 3.12 / FastAPI + Uvicorn / SQLAlchemy 2.0 (async) / PostgreSQL / arq (Redis) / 阿里云 OSS
- 前端：Vue 3 + Vite / Tailwind CSS v4 / Pinia

更详细的架构、目录结构、已实现功能见 [CLAUDE.md](CLAUDE.md)。

---

## 本地开发

### 后端（`backend/`）

```bash
uv sync

# 终端1：启动 FastAPI
uv run uvicorn app.main:app --reload

# 终端2：启动 Worker
uv run arq app.worker.settings.WorkerSettings
```

打开 Swagger：http://127.0.0.1:8000/docs

环境变量参考 [`.env.example`](.env.example)，复制为 `backend/.env` 并填好数据库 / Redis / OSS / DashScope / ToAPIS 等配置。

### 前端（`frontend/`）

```bash
npm install
npm run dev
```

默认通过 `VITE_API_BASE_URL=/api`，vite 开发代理转发到 `http://127.0.0.1:8000`。

---

## Docker 部署

`deploy/` 目录提供了打包到 Docker Hub 并在 1Panel（或任意 Docker 主机）上部署所需的全部文件：

```
backend/Dockerfile                # 后端镜像（API + worker 共用，命令不同）
frontend/Dockerfile               # 多阶段构建：node 编译 -> nginx 托管
frontend/nginx.conf               # SPA 路由 + /api/ 反代到 backend:8000
deploy/docker-compose.yml         # 本地构建/测试用（带 build）
deploy/docker-compose.1panel.yml  # 1Panel 服务器用（只拉镜像，不 build）
deploy/.env.example               # 环境变量模板
```

镜像命名：`kaiqi520666/shangtu-backend`、`kaiqi520666/shangtu-frontend`（`backend`/`worker` 两个服务共用同一个镜像，只是 `command` 不同）。

### 第一步：本地构建 + 推送到 Docker Hub

```bash
cd deploy
cp .env.example .env
# 编辑 .env，填好 POSTGRES_PASSWORD / SECRET_KEY / OSS_* / DASHSCOPE_* / TOAPIS_*

# 构建镜像
docker compose build

# 本地起一遍验证（可选）
docker compose up -d
# 浏览器访问 http://localhost:8080 测试登录/上传/生图
docker compose down

# 登录并推送（backend 和 worker 用同一镜像，推一次即可）
docker login
docker compose push backend frontend
```

### 第二步：1Panel 服务器准备

1. 1Panel 后台确认已安装 **Docker**
2. 在服务器上建一个目录，例如 `/opt/1panel/apps/shangtu/`
3. 把以下文件传到这个目录：
   - `deploy/docker-compose.1panel.yml` → 重命名为 `docker-compose.yml`
   - `deploy/.env`（本地编辑好的、含真实密钥的那份，**不要**用 `.env.example`）
4. 创建数据持久化目录：
   ```bash
   mkdir -p /opt/1panel/apps/shangtu/data/postgres /opt/1panel/apps/shangtu/data/redis
   ```

### 第三步：在 1Panel 里启动

**容器 → 编排（Compose）→ 创建编排**：

- 名称：`shangtu`
- 路径：选择上传的目录 `/opt/1panel/apps/shangtu`
- 创建后点 **启动**，会自动 `docker compose pull` 拉取镜像并启动 5 个容器（db / redis / backend / worker / frontend）

`frontend` 容器监听服务器的 `8080` 端口（整站含 `/api` 反代）。

### 第四步：绑定域名 / HTTPS（可选）

1Panel **网站 → 创建网站 → 反向代理**，代理地址填 `http://127.0.0.1:8080`，再用 1Panel 自带的 Let's Encrypt 申请证书。

### 第五步：首次初始化数据

数据库表由 `create_all` 自动建好，但提示词模板、模特库需要种子数据：

```bash
docker exec -it <backend容器名> python scripts/seed_prompt_templates.py
docker exec -it <backend容器名> python scripts/upload_outfit_models.py
```

（容器名前缀视编排项目名而定，用 `docker ps` 确认）

### 数据与备份

- **数据库数据**：PostgreSQL 数据存在 `data/postgres/`，备份打包这个目录即可（建议先 `docker compose stop db` 或用 `pg_dump` 做热备份）
- **Redis 数据**：`data/redis/`，是任务队列状态，丢失影响小
- **图片资源**：存在阿里云 OSS，不在容器里，不受部署影响

### 后续更新流程

```bash
# 本地
cd deploy && docker compose build && docker compose push backend frontend

# 1Panel：编排页面点「重新拉取镜像」，或在服务器上执行
docker compose pull && docker compose up -d
```
