# backend/AGENTS.md

本文件只适用于 `backend/`。仓库根目录 `AGENTS.md` 中的 MVP、极简代码、复用、Git 和跨端同步规则继续生效。

## 技术栈与进程模型

- Python 3.12+、FastAPI、SQLAlchemy 2.0 async、asyncpg、PostgreSQL。
- Redis + arq 承担异步生成任务；API 进程负责校验、持久化、扣费和入队，Worker 负责调用上游、轮询、落库和失败补偿。
- httpx 访问模型和媒体供应商，OSS 保存用户上传与生成媒体。
- uv 管理 Python 依赖和命令，不使用裸 `pip` 或 conda。
- pytest + pytest-asyncio 负责测试，测试目录包含 `tests/` 和 `app/` 内的 Worker 测试。

## 常用命令

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run arq app.worker.settings.WorkerSettings
uv run pytest
uv run python -m compileall app
```

- 后端改动至少运行 `uv run python -m compileall app`；业务逻辑改动同时运行相关 pytest，跨模块改动运行完整 `uv run pytest`。
- 新增依赖使用 `uv add <pkg>`；新增生产依赖前按根目录规则先说明方案并等待确认。
- `scripts/` 中的脚本统一用 `uv run python scripts/<name>.py` 执行。

## 应用架构

- `app/main.py` 是 API 入口：启动时写入默认计费设置、连接 Redis，并聚合业务路由；数据库结构统一通过 Alembic 迁移。
- `app/routers/` 是 HTTP 边界，负责鉴权依赖、请求校验、资源归属检查、事务编排和响应组装。
- `app/routers/admin/` 按后台资源拆文件，由 `admin/__init__.py` 聚合；所有后台接口使用超级管理员依赖并记录必要审计日志。
- `app/services/` 放跨路由或包含多步业务编排的服务，例如生成任务入队补偿、数字人资产和 HeyGen 生命周期。
- `app/core/` 放跨模块领域规则和基础设施适配，包括数据库、鉴权、积分、时间、OSS、供应商、提示词、目录、任务状态和媒体投影。
- `app/core/providers/` 只封装供应商协议；业务路由和 Worker 不应散写供应商 URL、鉴权头或错误解析。
- `app/models/` 是 SQLAlchemy model 的唯一事实来源；新增 model 后同步在 `app/models/__init__.py` 导出，并生成、审查对应 Alembic 迁移。
- `app/worker/` 放 arq 入口和任务实现。`settings.py` 注册可入队函数，图片、视频、HeyGen 和配音任务按领域拆文件。
- `app/schemas/` 放跨路由响应或请求模型；仅供单个后台模块使用的 schema 可留在 `routers/admin/schemas.py`。

## API 与事务约束

- API 统一返回 `app.schemas.response.Response` 的 `{ code, message, data }` 结构；成功用 `success(...)`，可预期业务失败用 `fail(...)`。
- 全局异常处理会记录原始异常并返回中文通用错误。不要把供应商原始响应、密钥或堆栈放进客户端消息。
- 鉴权统一复用 `app.core.deps` 的用户或超级管理员依赖；资源查询必须同时约束当前用户，不能只按资源 ID 查询。
- router 保持薄：跨路由复用或涉及扣费、入队、补偿的多步流程放到现有 service/core 模块。
- 涉及积分、任务状态和退款时，数据库写入必须处于清晰的 commit/rollback 边界。入队失败必须补偿已扣积分并标记任务失败。
- 实际扣费写入任务 `credit_cost`；失败退款只通过任务退款标记执行一次，不新增第二套退款判断。
- 时间统一使用 `app/core/time.py` 的 `utc_now()` 和 `to_utc_iso()`；不要新增 `datetime.now()`、`datetime.utcnow()` 或 `func.now()`。
- 数据库 schema 以当前 models 为准，干净环境由 `Base.metadata.create_all` 创建。当前 MVP 不维护运行时兼容分支或旧字段解析。

## 生成任务与快照

- `GenerationJob` 表达用户工作台，图片、视频和配音等 task 表达可独立执行和计费的生成单元。修改 job/task 关系时同步检查历史列表、详情恢复、归档和前端 `:jobId?` 路由。
- 单任务生成参数以 `settings_snapshot_json` 为事实来源；接口回显、Worker 执行和前端恢复必须读取同一份快照。
- 提示词快照统一通过 `app/core/prompt_snapshot.py` 和现有 builder 构造，不在 router/worker 手写另一种 shape。
- 商品图提示词通过目录、模板和 `generation_prompt_builder.py` 组装；视频提示词走对应 video builder。模型名统一从 `app/core/model_config.py` 读取。
- 单图重生创建新的 `ImageTask`，旧任务通过 `replaced_by_task_id` 指向新任务；工作台查询只返回当前版本。
- 任务状态展示统一复用 `task_state.py`、`media_projection.py` 和 Worker 状态同步逻辑，不在不同路由各写一套超时或终态映射。
- Worker 上游错误经 `worker/provider_errors.py` 等现有入口归一化成中文文案；原始错误只记录日志。
- 生成媒体落 OSS 和资产库时复用 `generated_media_storage.py` 及现有资产服务，避免任务完成但资产记录不一致。

## 外部资源与配置

- 环境变量在进程边界读取，不把密钥、真实账号或供应商响应写入仓库。
- OSS 访问统一通过 `app/core/oss.py`；媒体下载统一复用 `media_download.py`，不要在各 Worker 重写下载和上传流程。
- DashScope、视频供应商和 HeyGen 调用分别复用 `core/strategy/`、`core/providers/` 的客户端与错误类型。
- HeyGen avatar、voice、翻译语言和 CosyVoice voice 是后端目录资源；同步脚本、后台管理接口、用户选择接口和 Worker 必须共享同一份启用状态与标识语义。
- 计费和系统配置统一通过 `core/system_settings.py` 读取；不要在 router、service 或 Worker 硬编码价格。

## 脚本与测试

- `scripts/` 只保留当前仍需执行的种子、同步、导入导出、诊断或本地模拟脚本；一次性逻辑完成后删除，不建立长期迁移兼容体系。
- 种子脚本必须复用当前 model/core 规则，并可在干净数据库上得到确定结果；不要复制生产业务校验。
- 路由测试放 `tests/`，领域 helper 和 service 以最窄层级测试；Worker 测试不得调用真实供应商或真实 OSS。
- 修改 API payload、任务快照、状态或资产结构时，同步更新相关 model、router、service、worker、测试和前端 restore/display 逻辑。
- 提交前除范围内测试外运行仓库根目录要求的 `git diff --check`。
