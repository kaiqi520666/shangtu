# ShangTu 架构评审

评审时间：2026-06-28
评审方式：优先使用 CodeGraph。`codegraph_explore` MCP 已用于梳理整体调用链；本地 CLI 继续补充 `codegraph impact`、`codegraph callers`、`codegraph callees`。当前 CodeGraph 索引状态：200 files / 2,286 nodes / 6,099 edges，索引最新。

## 1. 整体架构图（文字调用链）

### 1.1 图片生成主链路

```text
Vue 页面
  frontend/src/views/generator/{product-suite,product-image,outfit,free-image}/*.vue
    ↓
场景 composable
  useProductSuiteGenerator / useProductImageGenerator / useOutfitGenerator / useFreeImageGenerator
    ↓
通用生成编排
  useGenerationRunner.ensureCurrentJob()
  useGenerationRunner.enqueueImageBatch()
  useGenerationCards.startPollingCard()
    ↓
前端 API 封装
  frontend/src/api/generation.js
  frontend/src/api/image.js
    ↓
FastAPI Router
  POST /generation/jobs        → backend/app/routers/generation.py:create_job
  PATCH /generation/jobs/{id}  → backend/app/routers/generation.py:update_job
  POST /image/generate         → backend/app/routers/image.py:create_task
  GET  /image/task/{id}        → backend/app/routers/image.py:get_task
    ↓
业务逻辑
  get_effective_image_credit_cost()
  deduct_user_credits()
  _build_image_task_prompt()
  build_image_generate_prompt()
  ImageTask / GenerationJob 落库
    ↓
队列
  request.app.state.redis_pool.enqueue_job("generate_image", ...)
  ARQ worker: backend/app/worker/settings.py:WorkerSettings
    ↓
Worker
  backend/app/worker/tasks.py:generate_image
    ↓
外部 AI
  ToAPIS /v1/images/generations 创建任务
  ToAPIS /v1/images/generations/{provider_task_id} 轮询结果
    ↓
结果物化
  materialize_to_oss()
  upload_image_bytes()
  Aliyun OSS
    ↓
状态回写
  update_task_in_db()
  Redis task:{id}:status/progress/result/error
    ↓
前端轮询刷新卡片
  useGenerationCards.pollCardOnce()
```

### 1.2 视频生成主链路

```text
Vue 页面
  frontend/src/views/generator/product-video/ProductVideoView.vue
    ↓
场景 composable
  frontend/src/composables/useProductVideoGenerator.js
    ↓
通用生成编排
  useGenerationRunner.enqueueMediaBatch()
  useGenerationCards.startPollingCard(getTask=getVideoTask)
    ↓
前端 API
  frontend/src/api/video.js
  frontend/src/api/generation.js
    ↓
FastAPI Router
  POST /video/generate  → backend/app/routers/video.py:create_video_task
  GET  /video/task/{id} → backend/app/routers/video.py:get_video_task
    ↓
业务逻辑
  _validate_video_inputs()
  _validate_aspect_ratio()
  get_effective_video_credit_cost()
  deduct_user_credits()
  build_video_generate_prompt()
  VideoTask / GenerationJob 落库
    ↓
队列
  enqueue_job("generate_video", ...)
    ↓
Worker
  backend/app/worker/tasks.py:generate_video
    ↓
外部 AI
  ToAPIS /v1/videos/generations 创建任务并轮询
    ↓
结果物化
  materialize_video_to_oss()
  upload_video_bytes()
  Aliyun OSS
    ↓
状态回写
  update_video_task_in_db()
  Redis video_task:{id}:status/progress/result/error
    ↓
前端轮询刷新视频卡片
```

### 1.3 策略生成与资产库链路

```text
策略生成：
Vue 场景 composable
  ↓ generateImageStrategy / generateVideoStrategy
backend/app/routers/image.py:image_strategy 或 backend/app/routers/video.py:video_strategy
  ↓
backend/app/core/image_prompt_builder.py:build_strategy_template_prompt
backend/app/core/product_catalog.py:get_catalog
backend/app/core/image_analyzer.py:generate_image_strategy / generate_video_strategy
  ↓
DashScope 兼容 chat/completions

资产库：
frontend/src/composables/useAssetLibrary.js
  ↓
frontend/src/api/asset.js
  ↓
backend/app/routers/asset.py:list_assets / batch_delete_assets
  ↓
ImageTask + VideoTask + GenerationJob union 查询
  ↓
删除时同步清理 Redis 缓存 key（best effort）
```

### 1.4 架构判断

- 当前整体是“前端场景 composable + 后端 router 直接编排业务 + ARQ worker 直接访问 AI/OSS/DB”的分层。
- 优点：MVP 下链路短、定位快，已有 `useGenerationRunner`、`useGenerationCards`、`useGenerationStrategyFlow` 等前端通用抽象，避免了每个生成页面完全重写。
- 主要风险：后端 router 和 worker 同时承担“应用服务层”职责，模型提供商、状态机、退款、OSS 上传、Redis key 约定散在多个函数里；新增生成模型或存储后端时不是替换一个 adapter，而是要改 router、worker、prompt、前端常量、状态查询多处。

## 2. 核心模块清单与职责边界

| 模块 | 主要 class/component/function | 当前职责 | 边界评价 |
| --- | --- | --- | --- |
| FastAPI 入口 | `backend/app/main.py:lifespan` | 建表、创建 Redis pool、挂载 routers | 边界偏薄，OK；但 `Base.metadata.create_all` 在应用启动执行，MVP 可接受，生产化后应与 schema 管理解耦 |
| 统一响应 | `backend/app/schemas/response.py:Response/success/fail` | 业务响应 envelope | 清晰但能力很薄；没有全局异常中间件，导致 router 各自 `try/except return fail()` |
| 生成任务聚合 | `backend/app/routers/generation.py:create_job/list_jobs/get_job/update_job/delete_job` | 管理 `GenerationJob`，聚合图片/视频子任务 | 职责基本清晰；但通过 `_task_model_for_scenario()` 把场景硬编码到 `ImageTask/VideoTask`，新增媒体类型会牵动多处 |
| 图片生成 Router | `backend/app/routers/image.py:create_task/get_task/regenerate_task` | 扣积分、建 `ImageTask`、生成 prompt、入队、查询 Redis+DB 状态、重生 | 边界过宽；router 同时做应用服务、状态机、事务补偿、Redis 协议，属于高风险入口 |
| 视频生成 Router | `backend/app/routers/video.py:create_video_task/get_video_task` | 视频校验、扣积分、建 `VideoTask`、入队、状态查询 | 与图片 router 大量同构但未共享；短期可维护，新增第三类媒体会复制风险 |
| Worker | `backend/app/worker/tasks.py:generate_image/generate_video` | 调 ToAPIS、轮询、下载、上传 OSS、回写 DB/Redis、失败退款 | 职责过重；一个文件 856 行，包含 provider adapter、storage adapter、任务状态机和退款逻辑 |
| OSS 封装 | `backend/app/core/oss.py:upload_image_bytes/upload_video_bytes` | OSS 配置、校验、object key、上传、URL 拼接 | 边界相对清晰；但直接绑定 Aliyun `oss2`，无 storage interface，切存储后端影响明显 |
| Prompt 构建 | `backend/app/core/image_prompt_builder.py:build_image_generate_prompt/build_video_generate_prompt` | 从 `GenerationJob`、模板、设置生成 prompt snapshot | 图片路径职责清晰；视频 `build_video_generate_prompt()` 暂时只是透传用户 prompt，图片/视频抽象不对称 |
| AI 策略/分析 | `backend/app/core/image_analyzer.py:generate_image_strategy/generate_video_strategy` | 组 prompt、调用 DashScope、解析 JSON | 文件过大且场景分支多；“策略模板 + API 调用 + JSON 修复/解析”耦合 |
| 积分 | `backend/app/core/user_credits.py:deduct_user_credits/refund_user_credits` | 原子扣减/退款 | 函数边界清晰；但消费/退款流水只在部分业务中有模型，生成扣费没有统一交易记录入口 |
| 前端 API | `frontend/src/api/request.js`、`image.js`、`video.js`、`generation.js` | axios 实例与接口封装 | API 层清晰；但错误提示没有在 interceptor/composable 层统一处理 |
| 前端生成编排 | `frontend/src/composables/useGenerationRunner.js` | job 创建/保存、批量建任务、卡片插入、创建失败处理 | 抽象价值高；但 483 行且承接图片/视频差异，新增媒体会继续增加参数复杂度 |
| 前端卡片轮询 | `frontend/src/composables/useGenerationCards.js` | 卡片状态、轮询、批次完成、恢复卡片 | 职责清晰，是项目里较好的共享抽象；影响面大，修改需重点回归所有生成页 |
| 前端场景 composable | `useProductSuiteGenerator/useProductImageGenerator/useOutfitGenerator/useProductVideoGenerator` | 场景配置、策略生成、snapshot、任务发起、恢复 | 业务聚合合理但文件过大（583/587/742/608 行），尤其 outfit 已变成“页面服务对象” |
| 资产库 | `backend/app/routers/asset.py:list_assets/batch_delete_assets` | 图片/视频资产 union 查询、批量删除 | 功能边界清楚；但 asset 查询手写 image/video union，新增媒体类型需改 SQL 与 payload |
| 管理后台任务列表 | `backend/app/routers/admin/image_tasks.py:list_image_tasks` | 图片/视频任务 union 管理列表 | 与资产库存在相似 union/payload 逻辑，媒体类型继续增加会快速膨胀 |

## 3. 耦合度与影响面分析

### 3.1 CodeGraph impact 结果

| 变更点 | CodeGraph impact | 结论 |
| --- | ---: | --- |
| `backend/app/routers/image.py:create_task` | 1 affected symbol | 函数本身没有被其他 Python 函数直接调用，HTTP 入口不体现真实业务影响；实际变更会影响所有图片生成场景 |
| `backend/app/routers/video.py:create_video_task` | 1 affected symbol | 同上，HTTP 边界掩盖真实影响 |
| `backend/app/worker/tasks.py:generate_image` | 4 affected symbols | 代码层入口只被 worker settings 引用，但它内部 callees 多达 19 个，是“低入度、高复杂度”风险 |
| `backend/app/worker/tasks.py:generate_video` | 3 affected symbols | 与 `generate_image` 类似，内部 callees 18 个 |
| `backend/app/models/ImageTask` | 33 affected symbols | 高影响核心模型；admin、asset、generation、image router、overview、utils 都依赖 |
| `backend/app/models/VideoTask` | 32 affected symbols | 高影响核心模型；与 ImageTask 平行扩散 |
| `backend/app/models/GenerationJob` | 33 affected symbols | 高影响聚合模型；prompt、generation、asset、admin、image/video router 均依赖 |
| `backend/app/core/oss.py:upload_image_bytes` | 16 affected symbols | OSS 图片上传被用户上传、系统模特、穿搭模特、worker 生成结果共用；变更需全链路回归 |
| `backend/app/worker/tasks.py:materialize_to_oss` | 5 affected symbols | 表面影响小，但它在 `generate_image` 成功路径中，失败会触发退款和任务失败 |
| `backend/app/core/image_prompt_builder.py:build_image_generate_prompt` | 10 affected symbols | 影响图片生成 prompt、路由、prompt invariant 脚本 |
| `frontend/src/composables/useGenerationRunner.js:useGenerationRunner` | 16 affected symbols | 被 5 个生成场景复用，属于前端核心编排点 |
| `frontend/src/composables/useGenerationCards.js:useGenerationCards` | 16 affected symbols | 被 5 个生成场景和对应页面依赖，轮询状态变更需全场景回归 |

### 3.2 `generate_image` / `generate_video` 的真实复杂度

CodeGraph `callees` 显示：

- `generate_image` 直接调用 `_set_progress`、`update_task_in_db`、`_mark_failed`、`fetch_task_user_id`、`validate_size`、`build_create_payload`、`extract_provider_task_id`、`extract_provider_error`、`extract_provider_status`、`extract_provider_progress`、`extract_result_url`、`_mark_timeout`、`materialize_to_oss`，并依赖 `TOAPIS_*` 常量。
- `generate_video` 直接调用 `_set_video_progress`、`update_video_task_in_db`、`_mark_video_failed`、`fetch_video_task_user_id`、`build_video_create_payload`、同一组 provider extractors、`_mark_video_timeout`、`materialize_video_to_oss`。

风险判断：

- 两个 Worker 函数的入度很低，但每个函数都同时覆盖“状态迁移、provider 协议、重试/轮询、OSS、退款、Redis 缓存、日志”。CodeGraph impact 低估了修改风险。
- `tasks.py` 里图片/视频是一对平行实现，而不是 `MediaTaskRunner + ProviderClient + StorageService`。任何 provider 返回结构变化，需要同时审查图片和视频两条路径。
- `normalize_provider_error()` 是少数统一错误处理点，但 `_mark_failed/_mark_video_failed/_mark_timeout/_mark_video_timeout`、Redis key、DB update 仍分裂为图片/视频两套。

### 3.3 高风险“改一处牵动多处”点

1. **任务模型字段变化：`ImageTask` / `VideoTask` / `GenerationJob`**
   - 影响 32-33 个符号。
   - 具体牵动：`generation.py` 聚合、`asset.py` 资产库、`admin/image_tasks.py` 管理列表、`image.py`/`video.py` 创建查询、worker DB update、前端 restore/display。
   - 风险：模型字段语义（如 status、progress、result_url、prompt_snapshot_json）没有领域服务封装，调用方直接读写。

2. **状态机与 Redis key 约定**
   - 图片 key：`task:{id}:status/progress/result/error`。
   - 视频 key：`video_task:{id}:status/progress/result/error`。
   - 具体牵动：`worker/tasks.py` 写入，`image.py:get_task` / `video.py:get_video_task` 读取，`asset.py:batch_delete_assets` 清理。
   - 风险：没有集中常量/状态仓储；新增状态或改 key 需要人工同步三处以上。

3. **生成 provider 绑定 ToAPIS**
   - `worker/tasks.py` 直接拼 `/v1/images/generations`、`/v1/videos/generations`，并内联 payload/status/result 提取。
   - `model_config.py` 只抽了模型名，没有抽 provider 客户端。
   - 风险：新增第二个图片生成模型/供应商时，不能只新增 adapter，需要改 payload 构造、状态解析、错误归一化、worker 分支和可能的前端选项。

4. **媒体类型分支散落**
   - `generation.py:_task_model_for_scenario()`、`asset.py:_image_asset_select/_video_asset_select()`、`admin/image_tasks.py:_image_task_select/_video_task_select()` 都知道 image/video 的字段差异。
   - 风险：新增音频/3D/多图批量等新媒体时，会复制 union 查询、payload、删除、管理后台过滤。

5. **前端生成编排核心**
   - `useGenerationRunner`、`useGenerationCards` impact 均为 16 affected symbols。
   - 风险：这是合理抽象，但没有测试覆盖；卡片状态、批次完成、轮询竞态任一改动会影响所有生成页。

## 4. 重复/相似实现

### 4.1 后端图片/视频创建任务重复

重复位置：

- `backend/app/routers/image.py:create_task`
- `backend/app/routers/video.py:create_video_task`
- `backend/app/routers/image.py:regenerate_task`

相似逻辑：

- 校验余额 → `deduct_user_credits()` → 创建任务行 → `db.commit()` → `enqueue_job()` → 入队失败退款并标记任务 failed。

风险：

- 图片、视频、重生任务的补偿逻辑都靠局部 `try/except` 手写；其中 `regenerate_task` 还有 TODO：“后续用 generation_attempts 做严格幂等退款”。
- 新增生成任务类型时很可能复制这一段，进一步放大扣费/退款不一致风险。

建议：

- 抽 `create_generation_attempt()` 或 `enqueue_generation_task()` 应用服务：统一扣费、建任务、入队、入队失败补偿、返回 payload。
- MVP 阶段可以先不引入复杂 attempts 表，但至少抽一个后端函数封装“扣积分 + commit + enqueue + compensate”。

### 4.2 后端图片/视频状态查询重复

重复位置：

- `backend/app/routers/image.py:get_task`
- `backend/app/routers/video.py:get_video_task`

相似逻辑：

- 读 DB 任务状态。
- pipeline 读 Redis status/error/progress/result。
- 避免 `done + result_url=null` 竞态。
- 返回 task payload 和当前积分。

风险：

- Redis/DB 状态合并规则复制两份，图片里对 “done 且 DB pending/processing 时必须有 redis_result_url 才认可” 的注释更完整；视频实现近似但不是同一个函数。
- 如果未来修竞态或新增状态，容易只改一条链路。

建议：

- 抽 `read_live_task_state(media_type, task, redis_pool)`，媒体差异只留 key prefix 和 payload 字段。

### 4.3 Worker 图片/视频失败处理重复

重复位置：

- `_mark_failed` / `_mark_timeout`
- `_mark_video_failed` / `_mark_video_timeout`
- `refund_task_credit` / `refund_video_task_credit`
- `update_task_in_db` / `update_video_task_in_db`
- `_set_progress` / `_set_video_progress`

风险：

- 这些函数都只是模型和 Redis key 前缀不同；当前重复已经超过 70%。
- 未来新增媒体类型会继续复制一组。

建议：

- 抽 `TaskStateRepository`：参数化 model、redis prefix、media_type。
- 抽 `refund_generation_credit(task_model, task_id)`，避免图片/视频退款逻辑双写。

### 4.4 资产库和管理后台 union 查询重复

重复位置：

- `backend/app/routers/asset.py:_image_asset_select/_video_asset_select`
- `backend/app/routers/admin/image_tasks.py:_image_task_select/_video_task_select`
- `backend/app/routers/generation.py:_image_task_payload/_video_task_payload`

风险：

- 三处都在手动把 `ImageTask` / `VideoTask` 映射成前端 payload，字段名与默认值靠人工对齐。
- 新增媒体字段时管理后台、资产库、历史恢复可能表现不一致。

建议：

- 抽 `media_task_projection.py`，统一 image/video 的 select label 与 payload builder。

### 4.5 前端错误提示重复

重复位置：

- `useGenerationRunner.js`
- `useProductImageGenerator.js`
- `useProductSuiteGenerator.js`
- `useOutfitGenerator.js`
- `useProductVideoGenerator.js`
- `RechargeModal.vue`

典型模式：

```javascript
const status = error.response?.status;
if (status === 401) {
  toast.error("登录已过期，请重新登录");
} else {
  toast.error(error.response?.data?.message || "xxx失败，请稍后重试");
}
```

风险：

- 401、业务错误、网络错误分散处理；message fallback 不一致。
- `frontend/src/api/request.js` 目前只做 token 注入和 credits 更新，没有错误归一化。

建议：

- 抽 `getApiErrorMessage(error, fallback)` 到 `frontend/src/utils` 或 `frontend/src/api/request.js` 附近。
- 不建议在 axios interceptor 里直接 toast（会耦合 UI），但可统一输出标准错误对象/消息函数。

### 4.6 前端场景 composable 结构重复

重复位置：

- `useProductImageGenerator.js` 587 行
- `useProductSuiteGenerator.js` 583 行
- `useOutfitGenerator.js` 742 行
- `useProductVideoGenerator.js` 608 行

相似结构：

- settings/reactive state
- `useGenerationCards()`
- `useGenerationStrategyFlow()`
- `useGenerationRunner()`
- `restoreJobData()`
- `triggerStrategyGeneration()`
- `confirmStrategyAndGenerate()`
- `build*Snapshot()`
- `normalize*StrategyItems()`

风险：

- 已经有通用 runner/strategy flow，但场景层仍偏“上帝 composable”。尤其 `useOutfitGenerator` 同时管理模特库 CRUD、场景策略、上传图、任务恢复、生成。
- 增加新场景时，大概率复制 500+ 行结构。

建议：

- 先抽轻量共享工具，不急着大框架化：
  - `cloneUploadedImages()`
  - `restoreCommonImageSettings()`
  - `validateUploadedMainImage()`
  - `handleApiErrorToast()`
  - `buildImageSnapshotPayload()`
- `useOutfitGenerator` 可拆 `useOutfitModels()`，把模特列表/上传/删除独立出去。

## 5. 异常处理与边界情况

### 5.1 已有机制

- Worker 有 `normalize_provider_error()`，可把上游英文/JSON 风格错误归一化为用户可读中文。
- Worker 失败会调用 `_mark_failed/_mark_timeout` 或视频对应函数：更新 DB、退积分、写 Redis error/status。
- 任务创建入队失败时，`image.py:create_task`、`video.py:create_video_task`、`image.py:regenerate_task` 都有退款补偿。
- 查询任务时，router 会同时看 DB 和 Redis，并防止 `status=done` 但 `result_url=null` 这种竞态直接展示给前端。
- `upload_image_bytes()` / `upload_video_bytes()` 对格式、空内容、大小做了校验。

### 5.2 风险与缺口

1. **没有统一异常边界**
   - 后端主要靠各 router 局部 `try/except return fail()`。
   - 未捕获异常会走 FastAPI 默认 500，与 `Response` envelope 不一致。
   - 建议：增加全局 exception handler，把未知异常统一转成 `Response(code=1)` 并记录日志；业务异常保留局部处理。

2. **OSS 上传失败会让任务失败并退款，但没有可恢复语义**
   - `materialize_to_oss()` 下载 provider 结果后上传 OSS；任一异常进入 `_mark_failed()`。
   - 如果 ToAPIS 已生成成功但 OSS 短暂失败，当前任务直接失败/退款，用户无法复用 provider 结果重试上传。
   - 建议：至少记录 `provider_task_id` 和原始 `final_url`（可短期存 error/context JSON），为后台补偿提供依据。

3. **AI 接口超时处理分散**
   - 图片 create timeout 60 秒，视频 create timeout 90 秒，轮询总时长分别 20/40 分钟。
   - HTTPError 轮询异常仅 print 后 continue，不区分持续 5xx、401、网络断连。
   - 建议：抽 provider client，集中处理 timeout/retry/backoff/error mapping。

4. **Redis 与 DB 双写没有强一致保证**
   - 当前通过“先 DB 后 Redis”降低 `done + result_url=null` 竞态，这是正确补丁。
   - 但状态仍是双写：worker 写 DB 与 Redis；router 合并读取；asset 删除 best effort 清 Redis。
   - 风险：Redis 过期/丢失不会影响最终 DB，但短期状态可能不一致；前端轮询异常被吞掉，用户只看到卡住。
   - 建议：以 DB 为最终状态源，Redis 只作进度缓存；封装读取规则并在进度长时间不变时给出可见错误或后台超时扫描。

5. **退款幂等部分存在，但创建补偿不是完整事务 outbox**
   - Worker 退款函数用 `credit_refunded` 和 `with_for_update()` 实现幂等，方向正确。
   - Router 入队失败在 DB commit 后发生，靠补偿退款；如果补偿本身失败，返回的 credits 可能是旧值。
   - 建议：MVP 可接受，但如果任务量上来，至少引入 outbox/attempt 状态来保证“任务已创建但未入队”可扫回。

6. **日志不可观测**
   - Worker 使用 `print()` 和 `traceback.print_exc()`，没有结构化日志、task_id/provider_task_id/context 字段体系。
   - 生产排查超时/上传失败/上游安全策略会困难。

## 6. 可扩展性隐患

### 6.1 新增图片生成模型/供应商

当前难点：

- `backend/app/core/model_config.py` 只配置模型名，不表达 provider 能力。
- `backend/app/worker/tasks.py` 直接写 ToAPIS URL、payload、status、result extractor。
- `backend/app/core/image_prompt_builder.py` 用 `IMAGE_GENERATE_MODEL` 查模板；模板与 provider/model 的耦合在 prompt 层。
- 前端 `frontend/src/constants/generator.js` 的 `resolutionMap` 与后端 `TOAPIS_SIZE_TABLE` 需要人工同步。

判断：**不容易扩展**。新增模型不是“注册一个 model”，而是改 provider payload、尺寸映射、模板匹配、worker 分支、可能还要改扣费配置。

建议：

- 抽 `ImageGenerationProvider` 接口：`create() / poll() / extract_result() / supported_sizes()`。
- 把 `TOAPIS_SIZE_TABLE` 与前端 `resolutionMap` 的来源统一，至少后端暴露 `/image/capabilities` 给前端。
- 模板查询可保留 model 维度，但 provider adapter 应拥有 model/capability 元数据。

### 6.2 新增视频模型

当前难点：

- `build_video_create_payload()` 直接绑定 `action`、`duration`、`aspect_ratio`、`resolution`、`image_urls/reference_images`。
- 前端 `productVideo.js` 的 `videoDemoTypes` 包含 demo URL、inputMode、业务类型；后端只校验 inputMode 和 aspect ratio，不知道 demo type 能力。

判断：**中等偏难**。如果新模型仍走 ToAPIS 兼容接口，改动可控；如果 provider 协议不同，需要拆 worker。

建议：

- 抽 `VideoGenerationProvider`。
- 把视频类型目录从前端常量迁到后端/数据库或至少与管理后台目录一致，否则前后端能力漂移。

### 6.3 新增存储后端

当前难点：

- `backend/app/core/oss.py` 直接 import `oss2`，函数名和异常类型都绑定 OSS。
- 调用方捕获 `OssConfigError`，错误语义与具体后端绑定。
- object key 生成、public URL 生成、上传校验都在一个文件里。

判断：**需要动多处命名和调用习惯**。实际调用点不算多（`upload_image_bytes` impact 16），但抽象语义已经写死 OSS。

建议：

- 保留当前实现，新增 `StorageConfigError`、`UploadedFile`、`upload_media_bytes()` 抽象；Aliyun OSS 作为默认实现。
- 调用方不要关心 OSS，只关心 storage upload 失败。

### 6.4 新增媒体类型

当前难点：

- `ImageTask` / `VideoTask` 是两张并列表。
- `GenerationJob` 通过 scenario 决定 task model。
- 管理后台、资产库、历史恢复都手写 image/video union。

判断：**会牵动非常多文件**。CodeGraph impact 已显示 `ImageTask/VideoTask/GenerationJob` 都是 32+ affected symbols。

建议：

- 如果近期只会有图片/视频，继续两表可以接受。
- 如果要新增第三种媒体，建议先抽 projection/service；不建议继续复制 `_audio_task_select()` 一路铺开。

## 7. 技术债清单（按严重程度排序）

### P0 / 高风险

1. **Worker 上帝模块**
   - 文件/函数：`backend/app/worker/tasks.py:generate_image`、`backend/app/worker/tasks.py:generate_video`
   - 问题：单文件 856 行，核心函数同时处理 provider 调用、轮询、状态机、OSS、退款、Redis。
   - 风险：新增 provider 或修复失败语义会牵动多段分支；CodeGraph callees 分别为 19/18 个。
   - 建议：先抽 `ProviderClient`、`TaskStateRepository`、`StorageService` 三块，逐步迁移。

2. **任务模型直接扩散**
   - 文件/函数：`backend/app/models/image_task.py:ImageTask`、`backend/app/models/video_task.py:VideoTask`、`backend/app/models/generation_job.py:GenerationJob`
   - 问题：CodeGraph impact 分别 33、32、33 affected symbols。
   - 风险：字段变更会影响 router、admin、asset、worker、prompt、前端恢复展示。
   - 建议：抽统一 payload/projection 与状态仓储，减少直接读写模型字段。

3. **扣费 + 建任务 + 入队补偿重复**
   - 文件/函数：`backend/app/routers/image.py:create_task`、`backend/app/routers/video.py:create_video_task`、`backend/app/routers/image.py:regenerate_task`
   - 问题：三处手写事务和补偿。
   - 风险：某个路径退款失败、状态标记不一致或漏写 error message。
   - 建议：抽后端应用服务统一处理。

4. **Redis/DB 状态协议散落**
   - 文件/函数：`backend/app/worker/tasks.py:_mark_failed/_mark_video_failed`、`backend/app/routers/image.py:get_task`、`backend/app/routers/video.py:get_video_task`、`backend/app/routers/asset.py:batch_delete_assets`
   - 问题：key prefix、status、result/error/progress 的读写规则没有集中定义。
   - 风险：改状态或清理逻辑时容易漏一个媒体类型。
   - 建议：集中到 `task_state.py`。

### P1 / 中高风险

5. **后端无统一异常处理**
   - 文件/函数：`backend/app/schemas/response.py:fail`、各 router 局部 `except Exception`
   - 问题：响应 envelope 和未捕获异常不统一，错误记录也不统一。
   - 风险：线上排查困难，前端 fallback message 不稳定。
   - 建议：加 FastAPI exception handler + 结构化日志。

6. **Provider 抽象缺失**
   - 文件/函数：`backend/app/worker/tasks.py:build_create_payload/build_video_create_payload/extract_result_url`
   - 问题：ToAPIS 协议硬编码。
   - 风险：新增模型/供应商会改核心 worker，而不是新增实现。
   - 建议：按 image/video 分 provider client。

7. **前后端能力配置重复**
   - 文件/函数：`backend/app/worker/tasks.py:TOAPIS_SIZE_TABLE`、`frontend/src/constants/generator.js:resolutionMap`
   - 问题：尺寸支持表手动双写。
   - 风险：一端新增 4K/比例后另一端未同步，导致前端可选但后端失败，或反之。
   - 建议：由后端 capability API 输出，前端消费。

8. **前端场景 composable 过大**
   - 文件/函数：`frontend/src/composables/useOutfitGenerator.js:useOutfitGenerator`、`useProductImageGenerator`、`useProductSuiteGenerator`、`useProductVideoGenerator`
   - 问题：单个 composable 500-700+ 行，混合配置、校验、策略、生成、恢复、上传/删除。
   - 风险：新增场景复制结构，局部修改容易破坏恢复/生成。
   - 建议：先拆 `useOutfitModels()` 与共享错误/上传/snapshot 工具。

9. **资产/管理后台 projection 重复**
   - 文件/函数：`backend/app/routers/asset.py:list_assets`、`backend/app/routers/admin/image_tasks.py:list_image_tasks`、`backend/app/routers/generation.py:get_job`
   - 问题：image/video 的 select label 和 payload 手写三遍。
   - 风险：字段漂移、过滤条件不一致。
   - 建议：抽 media task projection。

### P2 / 中风险

10. **前端错误 toast 处理重复**
    - 文件/函数：`frontend/src/composables/useGenerationRunner.js:ensureCurrentJob/loadHistoryTasks/loadGenerationJob/enqueueCreatedCard`、各场景 `triggerStrategyGeneration`
    - 问题：401 和业务错误重复判断。
    - 风险：提示不一致，后续国际化或错误码体系会很痛。
    - 建议：抽 `getApiErrorMessage()`。

11. **启动时自动建表**
    - 文件/函数：`backend/app/main.py:lifespan`
    - 问题：`Base.metadata.create_all` 与应用启动耦合。
    - 风险：MVP 可接受，但结构变更和生产权限管理会受限。
    - 建议：生产化前移到显式脚本/迁移命令。当前 MVP 规则允许破坏性 schema 变更，不必马上引入复杂迁移。

12. **日志体系薄**
    - 文件/函数：`backend/app/worker/tasks.py:generate_image/generate_video`
    - 问题：`print()` / `traceback.print_exc()`。
    - 风险：无法按 task_id/provider_task_id 聚合排查。
    - 建议：引入标准 logging 配置，至少保证 task_id、media_type、provider_task_id 出现在日志字段。

13. **OSS 命名泄漏到业务层**
    - 文件/函数：`backend/app/core/oss.py:OssConfigError`、调用方捕获处
    - 问题：业务层知道具体 OSS。
    - 风险：切存储后端需要改异常名、模块名、调用语义。
    - 建议：新增中性 storage API，Aliyun OSS 实现放到 adapter。

## 8. 推荐重构顺序

1. **先抽错误/状态基础设施，不改变业务行为**
   - `task_state.py`：统一 Redis key、状态读写、DB/Redis merge。
   - `api_error.js`：统一前端错误消息。

2. **再抽后端任务创建服务**
   - 统一图片/视频“扣费、建任务、入队、补偿”。
   - 保持现有表结构和 API payload 不变。

3. **拆 Worker provider/storage**
   - 先把 ToAPIS 调用移入 `toapis_provider.py`。
   - 再把 `materialize_*_to_oss` 移入 storage/service。

4. **最后治理媒体 projection**
   - 抽 image/video payload builder 和 union select。
   - 为新增媒体类型降低改动面。

总体判断：当前架构对 MVP 是能跑通的，前端已有一层不错的生成编排抽象；真正的架构风险集中在后端 worker 与任务状态/模型扩散。若短期只继续打磨图片/视频，建议优先做“状态仓储 + 创建任务服务”两个小抽象；若要接入新模型/新存储，必须先拆 provider/storage，否则每次扩展都会在核心链路上动刀，回归成本会越来越高。
