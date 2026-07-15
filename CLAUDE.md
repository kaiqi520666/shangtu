# CLAUDE.md

商图（ShangTu）：AI 电商内容生成 SaaS，覆盖商品图/套图、服饰穿搭、商品视频、数字人、配音、资产库和管理后台。后端 FastAPI + SQLAlchemy async + PostgreSQL + Redis(arq) + 阿里云 OSS；前端 Vue 3 SPA。

通用规则、技术栈、命令、架构与目录职责见 @AGENTS.md 以及 @backend/AGENTS.md、@frontend/AGENTS.md（同样适用于 Claude）。本文件只放这些 AGENTS.md 不包含、且无法直接从代码读出的信息，两处不要互相复制。

## 环境变量（后端 `.env`）

必需（缺失则后端启动即失败，见 `core/config.py` 的 `validate_runtime_config`）：

- `DATABASE_URL`（必须以 `postgresql+asyncpg://` 开头）、`REDIS_URL`、`SECRET_KEY`
- `VIDEO_PROVIDER`（`toapis` | `topenrouter`，默认 `topenrouter`）及对应密钥：`toapis` 需 `TOAPIS_KEY`；`topenrouter` 需 `TOPENROUTER_KEY` 或 `TOPENROUTER_API_KEY`
- 邮件（腾讯云 SES）：`TENCENT_CLOUD_SECRET_ID`、`TENCENT_CLOUD_SECRET_KEY`、`TENCENT_SES_FROM_EMAIL`、`TENCENT_SES_TEMPLATE_ID`（正整数）
- 人机验证（Cloudflare Turnstile）：`TURNSTILE_SITE_KEY`、`TURNSTILE_SECRET_KEY`

功能必需（启动不校验，但对应功能依赖它们）：

- OSS：`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_ENDPOINT`、`OSS_BUCKET_NAME`（用户上传与生成媒体落盘）
- DashScope：`DASHSCOPE_URL`、`DASHSCOPE_API_KEY`（图片分析、策略生成、提示词优化）；配音另需 `DASHSCOPE_TTS_URL`、`DASHSCOPE_TTS_MODEL`
- HeyGen：`HEYGEN_API_KEY`、`HEYGEN_BASE_URL`（数字人、视频翻译）
- 支付（ZPay）：`ZPAY_PID`、`ZPAY_KEY`、`ZPAY_GATEWAY`、`ZPAY_NOTIFY_URL`、`ZPAY_RETURN_URL`（积分充值）

可选：`OSS_PUBLIC_BASE_URL`（自定义 CDN 域名）、`TOAPIS_URL`、`TOPENROUTER_URL`、`TENCENT_SES_REGION`、`ARQ_JOB_TIMEOUT`、`ARQ_MAX_JOBS`、`LOG_LEVEL`；模型覆盖 `QWEN_TEXT_MODEL`、`IMAGE_GENERATE_MODEL`、`VIDEO_GENERATE_MODEL`（默认值在 `core/model_config.py`）。

扣费价格和充值套餐不走环境变量，在管理后台「系统设置」中配置；空库回退到后端代码默认值。

前端只读 `VITE_API_BASE_URL`（默认 `/api`，由 vite 代理到 `127.0.0.1:8000`）。

## 部署

- `backend/Dockerfile` 同一镜像两用：默认 `CMD` 跑 API（`uvicorn app.main:app`），worker 服务覆盖 `command` 为 `arq app.worker.settings.WorkerSettings`。
- `frontend/nginx.conf` 把 `/api/` 反代到 `backend:8000` 并去掉 `/api` 前缀，行为要和 vite 开发代理保持一致。
- `deploy/docker-compose.yml` 用于本地构建并推送镜像；`deploy/docker-compose.1panel.yml` 用于 1Panel 服务器，只拉取 Docker Hub 镜像不构建。二者都编排 db/redis/backend/worker/frontend，数据落盘在 `./data/postgres`、`./data/redis`。
- `deploy/initdb/001_shangtu_seed.sql.gz` 是手动导入用的种子库转储，未挂进 compose 的自动初始化目录。
- 目前 schema 由后端启动时 `Base.metadata.create_all` 建表（见 backend/AGENTS.md）——只能建新表，无法演进已有表结构；引入 Alembic 前先和用户确认云端数据取舍和生产 schema。

## 已知的坑

- DashScope 文本模型默认 `qwen3.6-flash`（`QWEN_TEXT_MODEL`），依赖 `enable_thinking=False` 关闭思考模式（`core/strategy/dashscope_client.py`）；换模型先确认这个参数仍兼容。
- 五个同步 LLM 接口（图片分析/策略、视频策略、图片/视频提示词优化）直连模型但**不扣积分**，已按用户+能力做 Redis 限流（`services/llm_rate_limit.py`），Redis 故障时 fail-open 放行。
- `DELETE /admin/outfit-models/{id}` 物理删 DB 记录但**不清理 OSS 文件**，会产生孤立文件；前端未开放此入口，停用统一走 `PATCH active=false`。
