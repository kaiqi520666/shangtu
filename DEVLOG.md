# DEVLOG

> Shangtu 项目开发日志。每完成一次有意义的改动，按时间倒序追加到顶部。
> 项目现状（已实现功能、目录、约定）见 [CLAUDE.md](CLAUDE.md)。

---

## 2026-06-12 — 商品套图父任务接入：刷新可恢复 + 同任务追加生成

- 后端 `/image/generate` `GenerateRequest` 增加可选 `job_id / type_id / title / sort_order`；带 `job_id` 时校验归属（属于当前用户）+ scenario（仅 `product_suite`），不存在/不匹配 → `fail("任务不存在")`；建 `ImageTask` 时透写四个字段；入队成功后若 `GenerationJob.status != 'generating'` 把它置为 `generating`；旧路径（不传 `job_id`）行为不变
- 不新增 `/generation/jobs/{id}/generate`，不做提交/删除/改名持久化，不做并发任务切换
- 前端 `api/generation.js`：`createGenerationJob(scenario)` / `listGenerationJobs(scenario)` / `getGenerationJob(jobId)` 三个调用；`api/image.js generateImage` 入参追加 `{job_id, type_id, title, sort_order}` 透传后端
- `useProductSuiteGenerator`：默认初始 `currentTaskTitle=''`，进入页面不创建 job；首次点击生成时 `ensureCurrentJob()` 延迟创建并把后端返回的 `title` 作为当前任务名；新增 `currentJobId / historyTasks / showHistoryDrawer / historyLoading / jobLoading / activeBatchRunId` 状态
- 同任务追加：`generateSuiteImages` 不再清 `outputCards`，新批次插到前面，`sortOrder = baseSortOrder + index` 接续递增，每张带 `batchRunId`；`maybeFinishGenerating` 改为只看 `activeBatchRunId` 这批是否全部进入终态，避免被旧 cards 干扰
- 新建任务 `createNewTask()`：`generating` 时拒绝；否则建一条 draft job 并清空 `uploadedImages / productInput / outputCards / genLogs / generatedCount / jobTotal / activeBatchRunId / suiteStructure→默认结构`，把 `currentJobId / currentTaskTitle` 切到新 job
- 恢复 `loadGenerationJob(jobId)`：拉详情后回填 `settings / source_images / input_text / structure`，把 `items` 转成 cards（`task_id` 同时作 `id` 与 `taskId`，`strategyTitle = item.title || getStructureName(type_id)`，`strategyContent = getStructureStrategy(type_id)`），非终态 cards 复用 `startPollingCard` 重新轮询，并打上同一个 `resumeBatchId`；`generating` 时拒绝切换
- UI：`GeneratorHeader` 删掉「批量托管」「生成记录」两个按钮（连带 `taskCount` props 与 `open-queue/open-history` emit），`GeneratorLayout` 同步去掉透传；`ProductSuiteWorkspace` header 右侧加 `+ 新建任务`（`generating` 时禁用）+ `生成记录`，批量下载继续仅在 `outputCards.length > 0` 时显示
- `ProductSuiteView` 接 `AppDrawer` 渲染历史列表：打开抽屉时拉 `listGenerationJobs`，点击 li 调 `loadGenerationJob`；列表显示 `title / 状态徽章（draft/generating/done/partial_failed/failed）/ created_at / total/completed/failed`
- 验证：① 后端端到端 — 创建 job(draft) → `/image/generate` 带 `job_id` 落 `image_tasks` 4 字段并把 job 切到 `generating`，再追加 3 张 `sort_order` 接续 `[0,1,2,3,4]`，列表 `total=5`；② 前端 `npm run lint`（oxlint + eslint）+ `npm run build` 全绿
- 旧库无新增 schema 变更（`image_tasks` 的四列在前次条目已加，`generation_jobs` 由 `create_all` 建好）

## 2026-06-12 — 后端父任务持久化：generation_jobs 表 + 三个只读接口

- 新增 `GenerationJob` 模型（`generation_jobs` 表）：`id/user_id/scenario/title/status/settings_json/source_images_json/input_text/structure_json/created_at/updated_at`，`status` 取 `draft/generating/done/partial_failed/failed`，当前 scenario 仅 `product_suite`
- `ImageTask` 增列 `job_id(36) / type_id(50) / title(100) / sort_order(int default 0)`，原字段不动；旧库需 `ALTER TABLE image_tasks ADD COLUMN job_id VARCHAR(36), ADD COLUMN type_id VARCHAR(50), ADD COLUMN title VARCHAR(100), ADD COLUMN sort_order INTEGER DEFAULT 0;`
- 新增 `routers/generation.py`，挂到 `/generation`：① `POST /jobs` 创建 draft 父任务（标题 `商品套图_YYYYMMDD_HHMMSS`）② `GET /jobs?scenario=...` 列表，按 `image_tasks.job_id` 聚合 `total/completed/failed`（done→completed，failed/timeout→failed）③ `GET /jobs/{id}` 详情含 `items[]`（按 `sort_order asc, created_at asc`），`settings/source_images/structure` 自动 `json.loads`
- 跨用户隔离：所有查询 `where user_id == current_user.id`，他人 `job_id` 取详情返回"任务不存在"
- 不动现有 `/image/generate`，不改前端，不做提交/删除/改名/真正生成提交接口
- 验证：用 `httpx.ASGITransport` + `app.router.lifespan_context` 端到端跑 6 例（创建 / 不支持的 scenario / 列表 / 详情 / 跨用户详情 / 跨用户列表 / 未登录 401）；插入 4 条 `image_tasks (done/done/failed/pending)` 后聚合得 `4/2/1`，items 排序 `[0,1,2,3]`，跨用户访问全部隔离

## 2026-06-12 — ToAPIS 尺寸映射清理：前后端统一用原生 ratio/resolution

- 前端 `resolutionMap` 重排为 `ratio → quality → [w,h]` 嵌套（与 ToAPIS 官方表对齐）：删除 `40:17`，新增 `2:1` / `1:2` / `9:21`；`4K` 仅 6 个比例（`16:9 / 9:16 / 2:1 / 1:2 / 21:9 / 9:21`）支持；`1:1 / 3:2 / 2:3 / 4:3 / 3:4 / 5:4 / 4:5` 不支持 4K
- 新增 `getSupportedQualities(ratio)` / `isQualitySupported(ratio, quality)` / `resolveQuality(ratio, quality)` 三个辅助；`ProductGenerationBasics.vue` 用 `isQualitySupported` 决定按钮禁用 + `不支持` 副标题，`watch(settings.ratio)` 切比例时若当前 quality 不被支持自动降级（优先 2K，回退 1K）
- `getCardSize` 不再 fallback 到 `1K/1:1`：先 `resolveQuality` 兜底修正 `settings.quality`，仍不可解则 throw，避免静默错误尺寸
- 前端 `generateImage` 签名 `{prompt, image_url, ratio, resolution}`，不再传 `size`；`useProductSuiteGenerator` 直接透传 `settings.ratio` / `settings.quality`，`width/height` 仅用于 `selectedImageLabel` 展示
- 后端 `GenerateRequest` 改为 `{prompt, image_url?, ratio="1:1", resolution="1K"}`，无 `size`；`ImageTask.size` 列继续保留，落库形如 `"9:16/1K"`，仅做审计标记
- `worker/tasks.py` 删除 `_RESOLUTION_MAP` / `SIZE_TO_RATIO_RESOLUTION` / `normalize_size` / `math` 导入；新增 `TOAPIS_SIZE_TABLE` + `validate_size(ratio, resolution)`，提交 ToAPIS 前严校验，未支持时直接 `failed` 并写 `error_message`（如 `"当前比例 1:1 不支持 4K，请选择 1K/2K"`），不打远端
- ToAPIS payload 直传 `size=ratio, resolution=resolution`（`gpt-image-2` 的 `size` 字段是比例字符串），`image_urls=[image_url]`
- 清理 APIYI 残留：`.env.example` 删除 `APIYI_KEY`，补 OSS / DashScope / TOAPIS 模板；代码层全项目 grep `APIYI|apiyi|gpt-image-2-vip` 零命中（DEVLOG 旧条目作为历史记录保留）
- 验证：`uv run python -c` 跑 `validate_size` 13 例 / `build_create_payload` 2 例 / `extract_*` 多例 / `TOAPIS_SIZE_TABLE` 4K 集合断言 全通过；`GenerateRequest` 无 `size` 字段；`from app.main import app` 与 `WorkerSettings` 导入正常；前端 `npm run lint` + `npm run build` 通过

## 2026-06-12 — 生图后端切换：APIYI → ToAPIS（异步任务流）

- `worker/tasks.py` 完整重写：APIYI 同步阻塞调用替换为 ToAPIS 异步任务流。流程：`POST {TOAPIS_URL}/v1/images/generations` 创建任务 → 5 秒一次轮询 `GET {TOAPIS_URL}/v1/images/generations/{provider_task_id}` → completed 后从 `data[0].url` 下载结果图 → `upload_image_bytes(..., source="generated")` 转存到我们 OSS → 落库 OSS URL。最长等待 20 分钟，超时本地任务标 `timeout`
- 状态映射：ToAPIS `queued/in_progress → processing`，`completed → done`（且 URL 有效），`failed/error/cancelled → failed`；失败时优先取 ToAPIS 返回的 `error.message`
- 错误分类（写 Redis `task:{id}:error` + DB `error_message`）：`TOAPIS_KEY` 缺失 / 创建任务失败 / 轮询超时 / ToAPIS 失败 / completed 无 URL / 下载结果图失败 / OSS 上传失败
- 进度：ToAPIS 返回 `progress` 时同步写 Redis `task:{id}:progress` + DB `image_tasks.progress`；`done` 强制 100
- 入参兼容：`generate_image` 新增 `ratio` / `resolution` 参数；`normalize_size()` 把旧格式 `"720x1280"` 通过 `SIZE_TO_RATIO_RESOLUTION`（与前端 `resolutionMap` 同步）反查 `(ratio, resolution)`；显式 `ratio`/`resolution` 优先；GCD 兜底解析任意 `WxH` 字符串
- `ImageTask` 表新增列：`provider`(默认 `toapis`) / `provider_task_id` / `error_message` / `progress`；旧库需手动 ALTER 补列
- `GenerateRequest` 新增 `ratio: str|None` / `resolution: str|None`，保留 `size: str = "720x1280"` 兼容；router enqueue 透传 `(prompt, size, image_url, ratio, resolution)`
- `GET /image/task/{task_id}` 响应新增 `progress` 字段（Redis `task:{id}:progress` 兜底，回退 DB；`done` 时强制 100）；其它字段形态不变，前端 UI 无需改
- `WorkerSettings.job_timeout` 由 330 提升到 1500，覆盖 20 分钟轮询 + 下载/上传缓冲
- `PRODUCT_IMAGE_SYSTEM_PROMPT` 由 messages 多模态形式改为前缀拼接到 `prompt`（ToAPIS 走 `prompt + image_urls`，无 messages 概念）
- 验证：`uv run python -c` 跑 `normalize_size` 8 例 / `normalize_content_type` 6 例 / `build_create_payload` 2 例 / `extract_provider_*` 多例全部通过；`from app.main import app` 与 `from app.worker.settings import WorkerSettings` 导入正常

## 2026-06-12 — 生成图转存 OSS（仅 worker）

- `worker/tasks.py` 不再把 APIYI 临时 url 或 b64_json 直接写入 `ImageTask.result_url`，统一调 `upload_image_bytes(..., source="generated")` 转存到我们的 OSS，最终落库的是 OSS 公网 URL，规避 APIYI 链接过期 / 图床下线
- 抽出 `extract_apiyi_image()` / `normalize_content_type()` / `materialize_to_oss()` 三个辅助函数；URL 分支 `httpx.AsyncClient.get` 下载 + 按 `Content-Type` 选 mime（容错 `image/jpg → image/jpeg`，未知/缺失回落 `image/png`）；b64_json 分支 `base64.b64decode(..., validate=True)`，content_type 固定 `image/png`
- 新增 `fetch_task_user_id(task_id)` 按 task_id 查 `ImageTask.user_id`，不依赖前端透传；查不到任务直接 failed
- 失败分类落 Redis `task:{id}:error`：下载失败（`httpx.HTTPError`）/ 解码失败（`ValueError` / `base64.binascii.Error`）/ OSS 上传失败（其它）三类
- DB→Redis 顺序保留前次 review 修复（先 DB `update_task_in_db("done", uploaded.url)` 再 Redis `status=done`）
- 路由 / 前端轮询 / `ImageTask` 表结构均无改动
- 验证：`uv run python -c` 跑 5 条 `extract_apiyi_image` + 5 条 `normalize_content_type` + `build_messages` 两条分支输出全部正确

## 2026-06-12 — 商品套图闭环 review 修复（一致性 + 健壮性）

- 后端 worker：先 `update_task_in_db("done", url)` 再写 Redis `status=done`，杜绝"前端读到 status=done 但 result_url=null 后停止轮询"的竞态
- 后端 `GET /image/task/{task_id}`：增加 `task:{id}:result` JSON 兜底解析；`status=done` 而 `result_url` 仍为空时降级返回 `processing`，让前端继续轮询
- 后端 `POST /image/generate`：扣积分 + 建任务合并到同一 commit，失败 rollback；入队失败时退回积分并把任务标 `failed`，避免"被扣积分但没活"
- 数据库：`image_tasks.prompt` 由 `String(1000)` 改为 `Text`（商品套图 prompt 易超 1000 字符）。已存在库需手动 ALTER：`ALTER TABLE image_tasks ALTER COLUMN prompt TYPE TEXT;`
- 前端轮询：`pollInFlight = Set<cardId>` 单飞锁 + 进入处理前再次校验 `TERMINAL_STATUSES`，避免慢响应叠加导致 `generatedCount += 1` 重复
- 前端进度：新增 `jobTotal` ref，`generateSuiteImages` 启动时锁定为 `queue.length`，`Workspace` 与 `SettingsPanel` 进度分母统一使用 `jobTotal || totalCount`，用户生成中改 `suiteStructure` 分母不再漂移
- UI：失败/超时卡片隐藏"放大预览/下载单张"按钮，改为底栏直接显示红色错误文案；非 done 卡片点击不再打开空预览模态
- 验证：`npm run lint`（0 warning）+ `npm run build` 通过；`uv run python -c` 校验 `prompt` 列类型 `TEXT`、router 路径未变

## 2026-06-12 — 商品套图打通真实生图闭环

- 前端 `api/image.js` 新增 `generateImage({prompt, size, image_url})` 与 `getImageTask(taskId)`（60s / 15s 超时）
- `useProductSuiteGenerator.generateSuiteImages` 重写：删除 Canvas mock 全套（`renderSuiteImage` / `paintSuiteBackground` / `paintProduct` / `paintSuiteCopy` / `getCopyLines` / `THEME_COLORS`），改为按 `buildSuiteQueue()` 展开队列（动态数量，由 `suiteStructure` enabled+count 决定，未写死张数），逐张 `POST /image/generate`（携带主图 OSS url），prompt 注入 platform/language/ratio/图类型/卖点要求 + 强约束；每张任务每 5 秒轮询一次；`outputCards` 新增 `taskId/status/resultUrl/errorMessage`；单张失败不影响其它任务；`onBeforeUnmount` 清空所有 setInterval
- 后端 `GET /image/task/{task_id}`：优先读取 Redis 实时状态 `task:{id}:status` 和 `task:{id}:error`，回退到 DB；响应增加 `error_message` 字段
- UI：`GeneratedCardGrid` 在 `card.dataUrl` 为空时按 `card.status` 显示 spinner / 红色错误提示；`ProductSuiteWorkspace` 把全屏遮罩改为只在"任务尚未创建"瞬间显示；按钮文案保持现有动态 `totalCount`，未写死张数
- 留白：未做单张重算真实接口、未引入 `generation_jobs` 表、未做历史记录、未做取消任务

## 2026-06-12 — `/image/generate` 支持带参考图生图（仅后端）

- `routers/image.py`：`GenerateRequest` 新增可选 `image_url: str | None`，入队时透传给 worker
- `worker/tasks.py`：`generate_image(ctx, task_id, prompt, size, image_url=None)` + `build_messages()` + `PRODUCT_IMAGE_SYSTEM_PROMPT`（电商商品图系统提示词，强约束以参考图为主体、不虚构品牌/认证/参数/价格）；`image_url` 存在时构造 `[system, user(text+image_url)]` 多模态 messages，缺省时保持纯文本生图
- 响应解析、状态机、`/image/task/{task_id}`、`ImageTask` 表结构均未改动

## 2026-06-12 — 商品套图打通"上传 OSS + AI 读图"

- 后端：`app/core/image_analyzer.py` 在 DashScope payload 顶层加 `enable_thinking: false`，关闭 qwen3.6 思考模式以降低延迟
- 前端新增 `src/api/image.js`（`uploadImage` / `analyzeImage`，单独设置 60s / 120s 超时，绕开全局 10s）
- `ImageUploader.vue` 改造：FileReader 仅做本地预览，并行调 `POST /image/upload`，向上 emit 结构化对象 `{ id, previewUrl, url, objectKey, contentType, size, uploading, error }`，附 loading 遮罩与错误提示；401 提示重新登录
- `useProductSuiteGenerator.generateSellingPointsWithAI`：读取主图 OSS url 调 `POST /image/analyze`（带 platform/language），返回 `data.content` 写入"商品卖点&要求"
- 兼容性：`useGenerator.js` / `useOutfitGenerator.js` 增加 `getImageSrc` 取 `previewUrl`/`url`，使旧 Canvas 渲染兼容新结构化对象

## 2026-06-11 — 初始化 CLAUDE.md

- 后端：认证 + 图片上传(OSS) + 图片分析(DashScope) + 异步生图任务(arq+apiyi) 接口全部就绪
- 前端：登录/注册页已对接后端；三大工作台 UI 全部成型，但生成链路尚未对接后端，仍为 Mock
- 同步动作：根目录新增 `.gitignore`，从 git 索引移除 `backend/.env`、`.DS_Store`（保留本地）
