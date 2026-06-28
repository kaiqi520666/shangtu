# backend/AGENTS.md

本文件只适用于 `backend/` 目录。通用 MVP、Git、复用和不兼容旧逻辑的规则见仓库根目录 `AGENTS.md`。

## 技术栈

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL
- Redis + arq worker
- 阿里云 OSS
- ToAPIS / DashScope 模型名由 `.env` 配置：`IMAGE_GENERATE_MODEL`、`VIDEO_GENERATE_MODEL`、`QWEN_TEXT_MODEL`

## 常用命令

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run arq app.worker.settings.WorkerSettings
uv run python -m compileall app
uv run python scripts/seed_product_catalog.py
```

## 后端规则

- Python 依赖管理统一用 `uv`，不要用裸 `pip install` 或 conda。
- API 统一返回 `{ code, message, data }` 响应壳；业务失败用 `fail(...)`。
- 时间统一使用 `app/core/time.py` 里的 `utc_now()` / `to_utc_iso()`，不要新增 `datetime.now()`、`datetime.utcnow()`、`func.now()`。
- 数据库 schema 以当前 SQLAlchemy models 为准；干净环境由 `Base.metadata.create_all` 创建。
- 不维护 Alembic、不维护运行时 schema 兼容补丁、不维护手动 SQL 文档；字段变化直接改 models 和调用方。
- 涉及积分扣减、退款、任务状态的代码必须保持事务一致性和幂等退款。
- Worker 上游错误只展示归一化后的中文友好文案，原始错误只进日志。
- OSS 环境变量只使用 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_ENDPOINT`、`OSS_BUCKET_NAME`、`OSS_PUBLIC_BASE_URL`。

## 生成任务规则

- 图片和视频任务都使用 `prompt_snapshot_json` 保存 `{ system, task, user, final, template_refs }`，不要新增拆散的 prompt 快照字段。
- 单任务参数事实来源是 `settings_snapshot_json`；接口返回和前端恢复都应使用该快照。
- 单图重生创建新 `ImageTask`，旧任务只写 `replaced_by_task_id` 指向新任务；工作台查询过滤旧版本。
- 图片、视频积分扣费都必须把本次实际扣费写入任务 `credit_cost`，失败退款只走 `credit_refunded` 幂等标记。
- 商品图提示词通过 `prompt_templates` + `app/core/generation_prompt_builder.py` 组装；商品视频生成只使用用户确认的可见提示词，视频提示词生成才走 `prompt_templates`。
- 生成链路使用 `app/core/model_config.py` 读取模型名，不在业务代码里散落硬编码模型字符串。

## 目录约定

- `app/routers/` 放 FastAPI 路由，按资源拆分，不把多个后台资源塞进同一个大文件。
- `app/routers/admin/` 放管理后台子资源；新增后台模块继续拆文件，再由 `app/routers/admin/__init__.py` 聚合。
- `app/models/` 放 SQLAlchemy models，字段变更直接同步调用方。
- `app/core/` 放跨路由复用的服务、工具和外部集成。
- `app/worker/` 放 arq worker 任务和上游轮询逻辑。
- `scripts/` 只放当前仍需要执行的种子、上传或模拟脚本，不保留一次性迁移脚本。

## 验证

- 修改后端代码后至少运行 `uv run python -m compileall app`。
- 改动 API payload、任务模型或生成链路时，同步检查对应前端 restore/display 逻辑。
