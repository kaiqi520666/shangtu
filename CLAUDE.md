# CLAUDE.md

Shangtu（商图）：AI 驱动的电商商品图批量生成 SaaS。后端 FastAPI + PostgreSQL + Redis(arq) + 阿里云 OSS；前端 Vue 3 SPA。

通用编码规范、技术栈细节、常用命令、后端/前端/数据规则、Git 规则见 @AGENTS.md（同样适用于 Claude）。本文件只放 AGENTS.md 不包含、且 Claude 无法直接从代码读出来的信息，不要在两个文件之间复制内容。

## 目录导航

```text
backend/app/
├── core/      # auth.py / database.py / deps.py / oss.py / image_analyzer.py
├── models/    # SQLAlchemy 模型，新增模型必须在 models/__init__.py 导出
├── routers/   # auth.py / image.py / generation.py / admin/ ...
├── worker/    # settings.py (WorkerSettings) / tasks.py (generate_image)
└── schemas/response.py   # 统一响应壳 {code, message, data}

frontend/src/
├── api/           # axios 调用统一走这里
├── composables/   # 业务逻辑放这里，组件保持薄
├── stores/        # Pinia
├── views/         # auth/ + generator/{product-suite|product-image|outfit|assets}/
└── components/    # 通用 UI 在 components/ui/，业务组件按场景分目录
```

## 环境变量（后端 `.env`）

必需：`DATABASE_URL`、`REDIS_URL`、`SECRET_KEY`、`OSS_ACCESS_KEY_ID/SECRET/ENDPOINT/BUCKET_NAME`、`DASHSCOPE_URL/API_KEY`、`TOAPIS_KEY`、`ZPAY_PID/KEY`。

可选：`OSS_PUBLIC_BASE_URL`（自定义 CDN 域名）、`TOAPIS_URL`（默认 `https://toapis.com`）。

扣费价格和充值套餐不走环境变量，在管理后台「系统设置」中配置；空库使用后端代码默认值。

前端只读 `VITE_API_BASE_URL`（默认 `/api`，由 vite 代理到 `127.0.0.1:8000`）。

## 部署

`backend/Dockerfile` 同一镜像通过覆盖 `command` 同时用作 API（`uvicorn`）和 worker（`arq app.worker.settings.WorkerSettings`）。`frontend/nginx.conf` 把 `/api/` 反代到 `backend:8000` 并去掉 `/api` 前缀，行为要和 vite 开发代理保持一致。`deploy/docker-compose.yml` 编排 db/redis/backend/worker/frontend，数据落盘在 `./data/postgres`、`./data/redis`。

## 已知的坑

- DashScope 模型 `qwen3.6-flash` 依赖 `enable_thinking=False` 关闭思考模式（`backend/app/core/image_analyzer.py`）；换模型先确认这个参数还兼容。
- 前端不要在组件里直接读 `localStorage`，统一走 `useAuth`。
- `DELETE /admin/outfit-models/{id}` 只删 DB 记录，不清理 OSS 上的图片文件，孤立文件需要人工/脚本定期清理。
