# CLAUDE.md

> Shangtu 项目"项目记忆"，给 AI Agent 快速理解项目现状用。
> **每完成一个功能/模块**：① 更新"已实现功能"对应条目；② 引入新依赖/环境变量/表字段时同步更新本文件；③ Mock 替换成真实接口时把"Mock"标记改成"已对接"。`DEVLOG.md` 已不再作为必维护文件，不要为了记录流水而更新它。

---

## 项目概述

**Shangtu（商图）** — AI 驱动的电商商品图批量生成 SaaS。上传商品图 + 选平台/尺寸 + AI 自动分析卖点，生成多种用途素材（主图、套图、详情图、服饰穿搭）。

- 阶段：**MVP**，前端 UI 大部分完成，后端核心生图链路已贯通；详情图 / 穿搭仍依赖前端 Mock
- 形态：前后端分离，前端 Vue 3 SPA，后端 FastAPI + PostgreSQL + Redis(arq) + 阿里云 OSS

---

## 技术栈

**后端** — Python 3.12+ / uv / FastAPI + Uvicorn / SQLAlchemy 2.0 (async + asyncpg) / PostgreSQL / arq (Redis) / 阿里云 OSS (`oss2`) / 生图 ToAPIS（`gpt-image-2`，异步任务流）/ 图像分析 DashScope（`qwen3.6-flash`，`enable_thinking=false`）/ JWT (`python-jose`) + bcrypt (`passlib`)

**前端** — Vue 3 + `<script setup>` / Vite 8 / Vue Router 懒加载 / Pinia + persistedstate（认证态目前自管 localStorage）/ Tailwind CSS v4 / `lucide-vue-next` / `vuedraggable` / axios（`api/request.js` 统一封装）/ oxlint + eslint + oxfmt / Node `^20.19.0 || >=22.12.0`

---

## 目录结构（关键路径）

```text
shangtu/
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI 入口，lifespan 注册 redis_pool / 自动建表
│   │   ├── core/                         # auth.py / database.py / deps.py / oss.py / image_analyzer.py
│   │   ├── models/                       # User / ImageTask / GenerationJob / PromptTemplate
│   │   ├── routers/                      # auth.py / image.py / generation.py
│   │   ├── schemas/response.py           # 统一响应壳 {code, message, data}
│   │   └── worker/                       # settings.py (WorkerSettings) / tasks.py (generate_image)
│   └── pyproject.toml / uv.lock / uv.toml
└── frontend/
    └── src/
        ├── router/index.js               # /login /register /generator/{product-suite|product-image|outfit}
        ├── api/                          # request.js / auth.js / image.js / generation.js
        ├── composables/                  # useAuth / useToast / useGenerator / useOutfitGenerator / useProductSuiteGenerator
        ├── views/                        # Home / Login / Register / Generator / ProductSuite / Outfit
        ├── components/                   # Generator* / Outfit* / ProductSuite* / AppModal / AppDrawer ...
        └── constants/                    # app.js / generator.js / outfit.js / productSuite.js
```

---

## 已实现功能

### 后端

#### 认证 `/auth`

- `POST /auth/register` / `POST /auth/login`：返回 JWT（30 天有效）+ user_id
- HTTPBearer + JWT，`get_current_user` 依赖注入

#### 图像 `/image`（需登录）

- `POST /image/upload`：multipart 上传 OSS（≤10MB，jpg/png/webp/gif），返回 `url` + `object_key`
- `POST /image/analyze`：DashScope `qwen3.6-flash` 多模态分析商品图，输出标准化产品名/卖点/适用人群/场景/参数
- `POST /image/generate`：扣 1 积分 + 建 `ImageTask(pending)` 同事务；接受 `{prompt, image_url?, ratio="1:1", resolution="1K", job_id?, type_id?, title?, sort_order=0}`，落库 `size = "{ratio}/{resolution}"` 仅作审计标记；入队失败退回积分 + 任务标 `failed` 且 `credit_refunded=True`；带 `job_id` 时校验归属 + scenario，入队成功后把 `GenerationJob.status` 置 `generating`；返回 `task_id`
- `GET /image/task/{task_id}`：优先读 Redis（`task:{id}:status` / `:error` / `:result` / `:progress`），回退 DB；`status=done` 但 `result_url` 缺失时降级为 `processing`，让前端继续轮询；响应字段 `{status, result_url, prompt, created_at, error_message, progress}`，`error_message` 是 worker 已归一化后的中文友好文案
- `GET /image/tasks`：当前用户历史任务（按 `created_at` desc）

#### 异步生图 Worker（`app/worker/tasks.py`）

- `generate_image(ctx, task_id, prompt, ratio, resolution, image_url=None)`：调 ToAPIS 异步任务流（`POST /v1/images/generations` 创建 → 5 秒一次轮询 `GET /v1/images/generations/{provider_task_id}`，最长等 20 分钟）→ completed 后从 `data[0].url` 下载结果图 → `upload_image_bytes(..., source="generated")` 转存到我们 OSS → 落库 `result_url` 是 OSS URL（不保存 ToAPIS 临时链接）
- 尺寸校验：`TOAPIS_SIZE_TABLE`（与前端 `resolutionMap` 完全对齐）严校验 `(ratio, resolution)`，未支持直接 failed + `error_message`（如 `"当前比例 1:1 不支持 4K，请选择 1K/2K"`），不打远端。4K 仅 `16:9 / 9:16 / 2:1 / 1:2 / 21:9 / 9:21` 支持
- 状态机：`pending → processing → done/failed/timeout`；ToAPIS `queued/in_progress` 映射 `processing`，`completed→done`，`failed→failed`
- 失败分类（写 Redis `task:{id}:error` + DB `error_message`）：`TOAPIS_KEY` 缺失 / 不支持的尺寸组合 / 创建失败 / 轮询超时 / 任务失败 / completed 无 URL / 下载失败 / OSS 上传失败
- **错误归一化**：`_mark_failed/_mark_timeout` 内部走 `normalize_provider_error`，把上游英文 JSON（如 `image_unsafe`、`upstream API failed`、`rate limit`、`timeout`）映射为中文友好文案，原始错误只 print 到日志；含中文的本地错误（如 `OSS 上传失败:` / `TOAPIS_KEY 未配置`）原样保留，但永远不向用户暴露原生英文 JSON
- **失败退积分**：`_mark_failed/_mark_timeout` 都会调 `refund_task_credit(task_id)`，幂等（行级锁 + `image_tasks.credit_refunded` 标志位），重复处理只退一次；done 路径不退；`/image/generate` 入队失败退分时也置 `credit_refunded=True`
- 进度同步：ToAPIS 返回 `progress` 时写入 Redis `task:{id}:progress` + DB `image_tasks.progress`，完成后强制 100
- 写入顺序：先 DB 再 Redis 终态，避免 `done` 但 `result_url` 空的竞态
- `image_url` 存在时 prompt 头部拼 `PRODUCT_IMAGE_SYSTEM_PROMPT` 强约束保持商品主体一致，并向 ToAPIS 传 `image_urls=[image_url]`；ToAPIS payload 的 `size` 字段是比例字符串（`"9:16"`），不是像素 `"720x1280"`
- 主动剥离 `HTTP[S]_PROXY`，避免 Windows 走代理失败

#### 父任务 `/generation`（需登录）

- `POST /generation/jobs`：scenario 当前仅支持 `product_suite`，自动生成标题 `商品套图_YYYYMMDD_HHMMSS`，落 `generation_jobs(status=draft)`，返回 `{job_id, scenario, title, status, created_at}`
- `GET /generation/jobs?scenario=...`：返回当前用户该场景的父任务列表（按 `created_at desc`），每条带 `total/completed/failed`（按 `image_tasks.job_id` 聚合，`done` 计 completed，`failed/timeout` 计 failed）
- `GET /generation/jobs/{job_id}`：返回父任务设置 + 子任务清单 `items[]`（含 `task_id/type_id/title/sort_order/status/progress/result_url/error_message/credit_refunded`，按 `sort_order asc, created_at asc`），`settings/source_images/structure` 为反序列化后的 JSON
- `PATCH /generation/jobs/{job_id}`：保存/恢复工作台快照。可选字段 `{title, settings, source_images, input_text, structure}`，传哪个改哪个；`settings/source_images/structure` 由后端 `json.dumps(..., ensure_ascii=False)` 写入对应 JSON 列；`title` 校验 1-100 字；只能改自己的 job；返回 `{job_id, scenario, title, status, updated_at}`
- 子任务关联：`image_tasks` 新增 `job_id / type_id / title / sort_order` 字段，由 `/image/generate` 在请求体里收到后写入；商品套图前端默认在第一次点击「生成」时延迟创建 job（`POST /generation/jobs`），再调 `PATCH /generation/jobs/{id}` 把当前左侧工作台（标题/平台·语言·比例·质量/上传图/卖点/套图结构）落盘成快照，然后 `/image/generate` 每张图入队；后续同 job 内多次点击追加生成（不清空旧 cards），sort_order 接续递增；当前**不做提交/删除/改名/独立提交接口**

#### 提示词模板（内部能力）

- 新增 `prompt_templates` 表和 `PromptTemplate` 模型，用于后续把固定提示词从代码迁到数据库；当前只完成基础设施，尚未接入 `/image/analyze`、`/image/product-image/strategy`、`/image/generate`
- 字段：`id / scenario / purpose / platform / type_id / model / name / content / version / active / created_at / updated_at`
- `scenario/platform/type_id` 可为空，表示通用模板；`purpose` 示例：`ai_write / strategy / image_generate / video_generate`；`model` 示例：`qwen3.6-flash / gpt-image-2`
- 内部查询服务：`app.core.prompt_templates.get_prompt_templates(db, scenario, purpose, platform, type_id, model)`，只取 `active=True` 且匹配 `purpose + model` 的模板；`scenario/platform/type_id` 使用"精确值或 NULL 通用模板"匹配，返回模板列表和按稳定顺序拼接后的 `content`
- 拼接顺序从通用到具体：通用用途模板 → 场景模板 → 平台模板 → 图种/模块模板 → 最精确模板；同优先级按 `version asc, created_at asc, id asc`
- 旧库立即使用可手动建表：

```sql
CREATE TABLE prompt_templates (
  id VARCHAR(36) PRIMARY KEY,
  scenario VARCHAR(32),
  purpose VARCHAR(32) NOT NULL,
  platform VARCHAR(64),
  type_id VARCHAR(50),
  model VARCHAR(64) NOT NULL,
  name VARCHAR(100) NOT NULL,
  content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_prompt_templates_lookup
  ON prompt_templates (purpose, model, scenario, platform, type_id, active);
```

#### 基础设施

- `Base.metadata.create_all` 启动建表（开发期，无 Alembic）
- 统一响应壳 `{code, message, data}`，业务错误 `code != 0`
- OSS 配置兼容 `OSS_*` / `ALIYUN_OSS_*` 两套环境变量名

### 前端

#### 路由与认证

- `/`、`/login`、`/register`、`/generator`（重定向 `product-suite`）、`/generator/{product-suite|product-image|outfit}`
- 登录/注册页已对接 `/auth/login`、`/auth/register`，登录态写 `localStorage.nodepass_auth_user`
- `useAuth` 封装登录/登出/读 token；axios 拦截器自动注 `Authorization: Bearer`

#### 工作台 UI 框架

- `GeneratorLayout` = `GeneratorHeader`（logo / 额度 / `UserMenu`，已删去批量托管 / 生成记录入口）+ `GeneratorSidebar`（三大模块切换）；生成记录入口下沉到各场景工作台 header 右侧
- 全局 `GlobalToast` + `useToast`；通用 `AppModal` / `AppDrawer` / `AppSelect`

#### 商品套图（默认入口，`/generator/product-suite`）

- 设置面板 `ProductSuiteSettingsPanel`（图片上传 / 平台 / 语言 / 比例 / 画质 / 商品输入 / `SuiteStructureConfigurator`）
- 工作区 `ProductSuiteWorkspace`：header 右侧 `+ 新建任务` / `生成记录` 按钮；进度展示、生成日志、卡片网格、批量下载（仅 `outputCards.length > 0` 时显示）、单卡缩放/下载；卡片支持 `pending/processing/done/failed/timeout` 状态蒙层
- **数据状态：上传 / AI 读图 / 批量生图全部已对接后端**。`generateSuiteImages`：按 `buildSuiteQueue()` 展开（动态数量，由 `suiteStructure.enabled + count` 决定），首次点击生成时若 `currentJobId` 为空先 `createGenerationJob('product_suite')`，逐张 `POST /image/generate` 并带 `job_id/type_id/title/sort_order`（带主图 OSS url），每 5 秒轮询；`pollInFlight` 单飞锁；`jobTotal` 启动时锁定 = `queue.length`，分母不漂移；同 job 内多次点击生成不清空旧 cards，新批次插到前面，每张带 `batchRunId`，`maybeFinishGenerating` 只看本批次终态；`onBeforeUnmount` 清理所有定时器
- 父任务持久化：`createNewTask()` 新建一条 job 并清空当前工作区（含 `uploadedImages/productInput/outputCards/genLogs/suiteStructure 默认结构`）；`生成记录` 抽屉调 `listGenerationJobs('product_suite')`，点击恢复 → `loadGenerationJob(jobId)` 把 `settings/source_images/structure/items` 写回 reactive 状态，未完成 items 自动重启 polling；标题统一来自后端，前端输入框改名只改本地（暂未做 PATCH 持久化）

#### 商品详情图（`/generator/product-image`）

- 两步式：① 设置 → ② `StrategyReviewPanel`（拖拽排序模块卡片）→ ③ 生成
- `ModuleSelector`（首屏/卖点/场景/多角度/细节/氛围/质保等）+ 长图预览模态、历史/队列抽屉、AI 卖点生成、单卡操作
- **数据状态：图片上传走 OSS；其余生成 / AI 帮写仍 Mock**

#### 服饰穿搭（`/generator/outfit`）

- 两步式：① 设置（服装上传 / `ModelSelector` / `ScenePresetSelector` / 自定义场景 / 比例）→ ② `OutfitSceneReviewPanel`（编辑 `OutfitPoseCard` 姿态卡片）→ ③ 生成
- 工作区 `OutfitWorkspace`：预览幻灯片、任务卡片、单卡操作
- **数据状态：图片上传走 OSS；其余仍 Mock**

---

## 环境变量（后端 `.env`）

```env
DATABASE_URL=postgresql+asyncpg://admin:123456@localhost/shangtu
REDIS_URL=redis://localhost:6379
SECRET_KEY=<JWT 签名密钥>

# 阿里云 OSS（OSS_* 或 ALIYUN_OSS_* 任一组）
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_ENDPOINT=
OSS_BUCKET_NAME=
OSS_PUBLIC_BASE_URL=          # 可选，自定义 CDN 域名

# DashScope 图像分析
DASHSCOPE_URL=                # 例：https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=

# ToAPIS 生图（gpt-image-2 异步任务）
TOAPIS_KEY=
TOAPIS_URL=                   # 可选，默认 https://toapis.com
```

前端只读 `VITE_API_BASE_URL`（默认 `/api`，由 vite 代理到 `127.0.0.1:8000`）。

---

## 启动命令

```bash
# 后端（在 backend/ 下）
uv sync
uv run uvicorn app.main:app --reload
uv run arq app.worker.settings.WorkerSettings   # 另起一个终端

# 前端（在 frontend/ 下）
npm install
npm run dev
```

---

## 代码风格速参

- **后端**：FastAPI 路由统一返回 `Response`；DB 走异步 Session；扣积分/写表用同一事务；新增模型在 `app/models/__init__.py` 导出
- **前端**：业务逻辑放 `composables/use*.js`，视图组件保持薄；常量进 `constants/`；axios 调用通过 `api/`；不要在组件中直接读 `localStorage`，走 `useAuth`

---

## 协作约定

- 每次完成任务（新增功能、修改功能、修复 bug）后，自动执行 `git commit`，commit message 简明描述本次变更，不需要询问

---

## 已知技术债

- 缺正式迁移工具（Alembic 待引入），靠 `Base.metadata.create_all`：旧库需手动补列 `ALTER TABLE image_tasks ADD COLUMN error_message TEXT, ADD COLUMN progress INTEGER DEFAULT 0, ADD COLUMN provider VARCHAR(32) DEFAULT 'toapis', ADD COLUMN provider_task_id VARCHAR(128);`（之前还需 `ALTER COLUMN prompt TYPE TEXT`）；新增父任务后还需补 `ALTER TABLE image_tasks ADD COLUMN job_id VARCHAR(36), ADD COLUMN type_id VARCHAR(50), ADD COLUMN title VARCHAR(100), ADD COLUMN sort_order INTEGER DEFAULT 0;`，新表 `generation_jobs` 由 `create_all` 自动建
- 详情图 / 穿搭工作台的"AI 帮写"和"批量生成"仍 Mock，待对接 `/image/analyze` 和 `/image/generate`
- 用户额度在 `GeneratorHeader` 是写死的 `1,280 点`，未读 `users.credits`
- `useAuth` 直读写 `localStorage`，未走 Pinia store
- DashScope 模型 `qwen3.6-flash` 通过 `enable_thinking=false` 关闭思考模式；切模型时记得复核该参数兼容性

---

## 开发日志

`DEVLOG.md` 已停止作为必维护文件；新的项目状态以本文件和实际代码为准。
