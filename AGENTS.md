# AGENTS.md

ShangTu（商图）是一个 AI 电商内容生成 SaaS，当前覆盖商品图、服饰穿搭图、商品视频、资产库和管理后台。本文只记录 Codex 在本仓库长期需要遵守的项目规则；项目历史、阶段性计划和临时上下文不要写进这里。

## 项目阶段：MVP

- 当前处于 MVP 阶段，无线上用户，无需考虑向后兼容、数据迁移、平滑升级。
- 禁止编写以下内容，除非我明确要求：
  - 兼容旧版本字段/接口的判断分支（如 if (oldField) {...} else {...}）
  - feature flag / 灰度开关
  - deprecated 标记 + 保留旧代码路径
  - 防御性的多版本数据结构解析
  - "为未来扩展预留"的抽象层、接口、配置项
- 发现需求变更时，直接修改/删除旧代码，不要并存新旧两套逻辑。
- 数据库字段变更：直接 ALTER/DROP，不写迁移兼容代码，迁移脚本本身可以是一次性、破坏性的。
- 如果你认为某处确实需要兼容处理，先停下来问我，不要自己决定写。

## 技术栈

后端：

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL
- Redis + arq worker
- 阿里云 OSS
- ToAPIS：`gpt-image-2`、`seedance-2`
- DashScope：`qwen3.6-flash`

前端：

- Vue 3 + `<script setup>`
- Vite
- Tailwind CSS
- lucide-vue-next
- axios
- JavaScript only，不使用 TypeScript

## 常用命令

后端：

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run arq app.worker.settings.WorkerSettings
uv run python -m compileall app
```

前端：

```bash
cd frontend
npm install
npm run dev
npm run build
```

验证优先级：

- 后端改动至少跑 `cd backend && uv run python -m compileall app`
- 前端改动至少跑 `cd frontend && npm run build`
- 提交前跑 `git diff --check`

## 通用编码规则

- 优先读现有实现，复用已有组件、composable、API helper、工具函数。
- 发现两处以上相似逻辑，优先抽共享函数/组件/composable，不复制粘贴改变量名。
- 不新增无必要依赖；新增生产依赖前先说明方案并等确认。
- 不写“以后可能用”的代码，不保留死代码。
- 不做无关重构；每次提交保持一个清晰主题。
- 注释只写能帮助理解复杂逻辑的内容，不写代码表面含义。
- Python 依赖管理统一用 `uv`，不要用裸 `pip install` 或 conda。

## 后端规则

- API 统一返回 `{ code, message, data }` 响应壳；业务失败用 `fail(...)`。
- 时间统一使用 `backend/app/core/time.py` 里的 `utc_now()` / `to_utc_iso()`，不要新增 `datetime.now()`、`datetime.utcnow()`、`func.now()`。
- 数据库 schema 以当前 SQLAlchemy models 为准；干净环境重新部署。
- 不维护 Alembic、不维护运行时 schema 兼容补丁、不维护手动 SQL 文档。
- 涉及积分扣减、退款、任务状态的代码必须保持事务一致性和幂等退款。
- Worker 上游错误只展示归一化后的中文友好文案，原始错误只进日志。

## 前端规则

- 业务状态和副作用优先放 composable，组件保持薄。
- 通用请求放 `frontend/src/api/`，不要在多个页面重复写同一请求逻辑。
- 通用 UI 放 `frontend/src/components/ui/`，业务组件放对应业务目录。
- 生成工作台优先复用现有 shell、卡片、上传、选择器、toast、confirm、runner、card actions。
- 不为视频/图片重复写两套相同的工作台逻辑；差异只放在真正不同的卡片、输入或接口适配层。
- 管理后台继续复用 `AdminLayoutView`、`AdminPagination`、`AppSelect`、`AppCheckbox`、`AppModal`、`GlobalConfirm`、`GlobalToast`。

## 数据和任务规则

- 数据结构以当前 models、schemas 和 API payload 为准；不要在 `AGENTS.md` 记录字段清单。
- 修改任务模型、快照结构或生成链路时，同步更新相关 model、router、worker、frontend restore/display 逻辑。
- 删除或替换旧数据结构时，直接改调用方，不保留新旧结构并行解析。

## Git 规则

- 每次完成代码修改后自动提交，commit message 简明描述本次改动。
- 不使用 `git reset --hard`、`git checkout --` 等破坏性命令，除非用户明确要求。
- 不回滚用户未要求回滚的改动。
- 提交前自查 diff，确认没有夹带无关文件或生成产物。
