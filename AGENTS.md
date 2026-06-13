# AGENTS.md

给新开的 AI / Codex / Claude 窗口快速接手 Shangtu 项目用。  
更完整的项目记忆见 [CLAUDE.md](CLAUDE.md)。

## 项目定位

Shangtu（商图）是一个 AI 电商商品图生成 SaaS：

- 上传商品图到阿里云 OSS
- AI 读图生成商品卖点
- 按平台、比例、画质和图种批量生成商品图片
- 生图走 ToAPIS `gpt-image-2` 异步任务
- 后端负责轮询上游、转存 OSS、持久化任务、失败退款
- 前端负责工作台、任务恢复、生成记录、卡片轮询、下载和编辑重生

当前是 MVP 阶段。商品套图链路已经是真实后端闭环；商品详情图/服饰穿搭仍在逐步从 Mock 切到真实任务体系。

## 技术栈

后端：

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- PostgreSQL
- Redis + arq worker
- 阿里云 OSS (`oss2`)
- ToAPIS `gpt-image-2`
- DashScope `qwen3.6-flash`
- JWT (`python-jose`) + bcrypt (`passlib`)

前端：

- Vue 3 + `<script setup>`
- Vite 8
- Vue Router
- Tailwind CSS v4
- lucide-vue-next
- axios
- JSZip
- oxlint / eslint / oxfmt

## 关键目录

```text
backend/app/
├── main.py                  # FastAPI 入口，注册 routers，lifespan 初始化 Redis
├── core/
│   ├── auth.py              # JWT / 密码
│   ├── database.py          # async engine / session
│   ├── deps.py              # get_current_user / get_db
│   ├── image_analyzer.py    # DashScope AI 读图
│   ├── prompt_templates.py  # 提示词模板查询服务
│   ├── oss.py               # OSS 上传
│   └── time.py              # UTC 时间工具 utc_now / to_utc_iso
├── models/
│   ├── user.py
│   ├── image_task.py
│   ├── generation_job.py
│   └── prompt_template.py
├── routers/
│   ├── auth.py
│   ├── image.py             # 上传 / AI读图 / 生图任务 / 单图删除重生下载
│   ├── generation.py        # 父任务 job CRUD / 工作台快照
│   └── asset.py             # 资产库列表 / 批量删除
├── schemas/response.py      # 统一响应壳 {code, message, data}
└── worker/
    ├── settings.py          # arq WorkerSettings
    └── tasks.py             # generate_image 后台任务

backend/scripts/
└── seed_prompt_templates.py  # 幂等写入第一批提示词模板种子数据

frontend/src/
├── api/
│   ├── request.js
│   ├── auth.js
│   ├── image.js
│   ├── generation.js
│   └── asset.js
├── composables/
│   ├── useAuth.js
│   ├── useToast.js
│   ├── useConfirm.js
│   ├── useGenerationCards.js
│   ├── useCardActions.js
│   ├── useProductSuiteGenerator.js
│   ├── useGenerator.js
│   ├── useOutfitGenerator.js
│   └── useAssetLibrary.js
├── views/
│   ├── auth/
│   │   ├── LoginView.vue
│   │   └── RegisterView.vue
│   ├── generator/
│   │   ├── product-suite/ProductSuiteView.vue
│   │   ├── product-image/ProductImageView.vue
│   │   ├── outfit/OutfitView.vue
│   │   └── assets/AssetLibraryView.vue
│   └── HomeView.vue
├── components/
└── constants/
```

## 后端现状

统一响应格式：

```json
{ "code": 0, "message": "success", "data": {} }
```

业务失败使用 `fail(...)`，通常是 `code != 0`，不要随意改成裸 HTTP error。

核心接口：

- `POST /auth/register`
- `POST /auth/login`
- `POST /image/upload`
- `POST /image/analyze`
- `POST /image/generate`
- `GET /image/task/{task_id}`
- `GET /image/task/{task_id}/download`
- `DELETE /image/task/{task_id}`
- `POST /image/task/{task_id}/regenerate`
- `POST /generation/jobs`
- `GET /generation/jobs?scenario=...`
- `GET /generation/jobs/{job_id}`
- `PATCH /generation/jobs/{job_id}`
- `DELETE /generation/jobs/{job_id}`
- `GET /asset/list`
- `DELETE /asset/batch`

### GenerationJob / ImageTask

`GenerationJob` 是父任务/工作台：

- `scenario`
- `title`
- `status`
- `settings_json`
- `source_images_json`
- `input_text`
- `structure_json`
- `archived`
- `created_at`
- `updated_at`

`ImageTask` 是单张图任务：

- `job_id`
- `type_id`
- `title`
- `sort_order`
- `prompt`
- `size = "{ratio}/{resolution}"`
- `status = pending | processing | done | failed | timeout`
- `result_url`
- `error_message`
- `progress`
- `provider_task_id`
- `credit_refunded`
- `edit_instruction`
- `system_prompt_snapshot`
- `task_prompt_snapshot`
- `user_prompt`
- `prompt_template_refs_json`
- `archived`

场景目前后端已支持：

- `product_suite`
- `product_image`

`/image/generate` 允许上述场景的 job。Worker 不关心场景，只处理 prompt、尺寸、参考图和任务 ID。

### PromptTemplate

`prompt_templates` 是后端内部提示词模板表，当前只作为基础设施和种子数据存在，尚未接入现有生成链路。

- 查询服务：`backend/app/core/prompt_templates.py`
- 种子脚本：`backend/scripts/seed_prompt_templates.py`
- 执行方式：在 `backend/` 下运行 `.\.venv\Scripts\python.exe scripts\seed_prompt_templates.py`
- 当前 seed 覆盖通用生图规则、前端平台列表的平台专属规则、商品套图图种默认提示词、商品详情图模块默认提示词、AI 帮写和详情图策略提示词。
- 商品套图和商品详情图 `/image/generate` 已优先接入 `image_generate` 模板拼接：通用规则 + 场景规则 + 平台规则 + 图种默认用户提示词 + 用户提示词，最终完整 prompt 仍写入 `image_tasks.prompt`。
- AI 帮写已接 `ai_write` 模板；商品详情图策略生成已接 `strategy` 模板。

### 生图任务流

前端调 `/image/generate` 后：

1. 后端扣 1 积分并创建 `ImageTask(pending)`
2. 入队 Redis/arq：`generate_image`
3. worker 设置 `processing`
4. 调 ToAPIS 创建远端任务
5. 每 5 秒轮询 ToAPIS，最长 20 分钟
6. 成功后下载上游图片
7. 上传到自己的 OSS
8. DB 写入 `result_url`
9. Redis 写 `status=done` 和 `result`

失败/超时：

- worker 会归一化上游错误为中文友好文案
- 失败会通过 `refund_task_credit` 幂等退款
- 原始上游错误只打印日志，不直接展示给用户

### 时间约定

后端时间已明确 UTC：

- `backend/app/core/time.py`
- `utc_now()`
- `to_utc_iso()`
- 相关模型字段已改为 `DateTime(timezone=True)`
- 用户已经手动把 PostgreSQL 字段迁移成 `TIMESTAMPTZ`

不要再新增 `datetime.now()`、`datetime.utcnow()`、`func.now()`。新增时间写入统一用 `utc_now()`，接口返回时间统一用 `to_utc_iso()`。

## 前端现状

### 路由

当前主要路由：

- `/login`
- `/register`
- `/generator/product-suite/:jobId?`
- `/generator/product-image`
- `/generator/outfit`
- `/generator/assets`

### 商品套图

商品套图是当前最完整的真实链路。

入口：

- `frontend/src/views/generator/product-suite/ProductSuiteView.vue`
- `frontend/src/composables/useProductSuiteGenerator.js`
- `frontend/src/constants/productSuite.js`

能力：

- 上传商品图到 OSS
- AI 帮写商品卖点
- 配置平台、排版语言、比例、画质
- 配置白底图、场景图、卖点图、细节图数量
- 第一次生成自动创建 `product_suite` job
- URL 恢复：`/generator/product-suite/:jobId`
- 生成记录抽屉
- 同一个 job 内可多次生成，追加新图片，不清空旧图
- 卡片轮询
- 失败展示和失败不扣积分提示
- 单图下载、批量 zip 下载
- 单图删除
- 单图编辑重新生成，复用原图作为参考图，成功后替换原卡片图片

### 通用前端 composable

`useGenerationCards.js`：

- `outputCards`
- `genLogs`
- `generating`
- `generatedCount`
- `jobTotal`
- `activeBatchRunId`
- `startPollingCard`
- `pollCardOnce`
- `clearAllPollTimers`
- `maybeFinishGenerating`
- `createCard`

`useCardActions.js`：

- `zoomCard`
- `selectedCards`
- `selectedCardsCount`
- `toggleCardSelection`
- `toggleSelectAllCards`
- `downloadSingleImage`
- `batchDownload`
- `downloadAsZip`

新增场景时优先组合这两个 composable，不要复制商品套图里轮询/下载逻辑。

### 商品详情图

路由和旧页面存在，但生成逻辑仍主要来自旧 Mock 工作台。后端已支持 `product_image` 场景。下一步应该做：

- 新的 `ProductImageView`
- 新的 `useProductImageGenerator`
- 复用 `useGenerationCards`
- 复用 `useCardActions`
- 使用 `scenario = "product_image"`
- 支持 `/generator/product-image/:jobId?`
- 接入 `GenerationJob + ImageTask` 闭环

第一版不要做长图拼接、拖拽排序、模块策略二次编辑，先跑通任务闭环。

### 资产库

入口：

- `/generator/assets`
- `frontend/src/views/generator/assets/AssetLibraryView.vue`
- `frontend/src/composables/useAssetLibrary.js`
- `frontend/src/components/AssetCardGrid.vue`
- 后端 `backend/app/routers/asset.py`

能力：

- 分页列出当前用户已完成图片
- 按 `product_suite / product_image / outfit` 筛选
- 大图预览
- 单张下载
- 批量 zip 下载
- 批量删除

注意：当前资产库删除接口是硬删除 `ImageTask` 记录，但不物理删除 OSS 文件。后续最好改成软删除或补 OSS 物理删除能力，避免“永久删除”语义不一致。

### 服饰穿搭模特库

入口：

- 前端 `frontend/src/composables/useOutfitGenerator.js`
- 前端接口 `frontend/src/api/outfit.js`
- 后端接口 `backend/app/routers/outfit.py`
- 后端模型 `backend/app/models/outfit_model.py`
- 上传脚本 `backend/scripts/upload_outfit_models.py`

能力：

- `GET /outfit/models` 返回 active 模特列表
- 图片存 OSS，元数据存 `outfit_models`
- 前端按后端返回顺序显示，后端按 `sort_order asc, created_at asc` 排序
- 本地 `frontend/public/model/` 只作为上传源，不要提交到 git

## 常用命令

后端：

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run arq app.worker.settings.WorkerSettings
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe scripts\upload_outfit_models.py
```

前端：

```powershell
cd frontend
npm install
npm run dev
npm run build
```

注意：`npm run lint` 会带 `--fix`，可能改文件。只想验证时优先跑 `npm run build`。

## 环境变量

后端 `.env` 关键项：

```env
DATABASE_URL=
REDIS_URL=
SECRET_KEY=

OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_ENDPOINT=
OSS_BUCKET_NAME=
OSS_PUBLIC_BASE_URL=

DASHSCOPE_URL=
DASHSCOPE_API_KEY=

TOAPIS_KEY=
TOAPIS_URL=https://toapis.com
```

前端：

```env
VITE_API_BASE_URL=
```

## 编码和编辑约定

- 除非用户明确打出“执行”两个字，否则只讨论和分析，不要修改代码、配置、文档或运行会改变项目状态的命令。
- Windows 环境读取文件用：
  `Get-Content <path> -Encoding UTF8`
- 不要用 `cat` / `type` 读中文文件，容易乱码。
- 手工编辑文件优先用 `apply_patch`。
- 不要随意重置用户改动，不要使用 `git reset --hard`。
- 每次完成任务（新增功能、修改功能、修复 bug）后，自动执行 `git commit`，commit message 简明描述本次变更，不需要询问。
- `DEVLOG.md` 已不再作为必维护文件；完成任务后不要为了记录流水而更新它。
- 后端接口保持统一响应壳。
- 前端业务逻辑尽量放 composables，组件保持薄。
- 新增场景时优先复用 `useGenerationCards` / `useCardActions`。
- 新增后端时间字段或返回时间时，统一用 `utc_now()` / `to_utc_iso()`。

## 最小改动与溯源规则

- 遇到异常展示、异常文案、异常字段或异常行为时，必须先定位来源：后端返回 / 大模型返回 / 前端拼接 / 前端状态加工 / 历史脏数据。
- 未定位来源前，不要提出多层兜底方案，不要同时建议前端过滤、后端清洗、提示词修改等多处改动。
- 如果问题由本项目代码主动生成，优先删除或修正源头，不要额外增加防御层。
- 除非用户明确要求增强鲁棒性，否则不要为单点问题扩大改动面。
- 给修改建议时必须先说明：来源、原因、最小改动点、影响范围、是否需要改前端/后端。

## 已知技术债

- 没有 Alembic，开发期依赖 `Base.metadata.create_all`，旧库字段需要手动迁移。提示词快照字段旧库需补：`ALTER TABLE image_tasks ADD COLUMN IF NOT EXISTS system_prompt_snapshot TEXT, ADD COLUMN IF NOT EXISTS task_prompt_snapshot TEXT, ADD COLUMN IF NOT EXISTS user_prompt TEXT, ADD COLUMN IF NOT EXISTS prompt_template_refs_json TEXT;`
- 商品详情图和服饰穿搭还没有完全接入真实生图任务闭环。
- 资产库删除目前只删 DB 记录，不删 OSS 文件。
- 用户额度前端展示还没有完全从后端实时读取。
- `useAuth` 仍直接读写 `localStorage`，没有完全 Pinia 化。
- 资产库 / 详情图还需要更多端到端验证。

## 给新 Agent 的建议

接手时优先看：

1. [CLAUDE.md](CLAUDE.md)
2. `frontend/src/composables/useProductSuiteGenerator.js`
3. `frontend/src/composables/useGenerationCards.js`
4. `frontend/src/composables/useCardActions.js`
5. `backend/app/routers/image.py`
6. `backend/app/routers/generation.py`
7. `backend/app/worker/tasks.py`

如果要继续做商品详情图，不要从旧 `useGenerator.js` 直接复制大块 Mock 逻辑。应该以商品套图的真实任务闭环为模板，组合通用 composable，再只写详情图自己的结构、队列和 prompt。
