# 命名与分层评审

## 审阅来源

- 已先执行 `codegraph --help`，确认可用子命令包括 `files`、`node`、`explore`。
- 当前 MCP 工具列表未暴露独立的 `codegraph_files` 工具，因此使用同一索引能力的 `codegraph files` CLI 获取目录树，没有使用 `ls/find`。
- 索引统计：`frontend` 138 个文件，`backend` 73 个文件。
- 重点抽样：`backend/app/routers/image_generation.py`、`backend/app/routers/video.py`、`backend/app/routers/generation.py`、`backend/app/worker/tasks.py`、`frontend/src/router/routes/generator.js`、`frontend/src/api/image.js`、`frontend/src/api/video.js`、各 generator view。

本文已删除已完成的整改项，仅保留仍需要继续拆分或统一命名的位置。

## 1. 目录层次合理性

### 前端

整体顶层目录清晰：`views` 管页面入口，`components` 管 UI 组件，`composables` 管状态和副作用，`api` 管请求，`stores` 管 Pinia，全局工具在 `utils`。新人从 `frontend/src/router/routes/generator.js` 可以快速跳到商品套图、详情图、视频、穿搭、自由生图页面。

主要问题是“技术类型目录 + 业务领域目录”混用后，单个业务的代码分散过多：

- `frontend/src/views/generator/product-image/ProductImageView.vue`
- `frontend/src/components/product-image/ProductImageSettingsPanel.vue`
- `frontend/src/composables/generator/useProductImageGenerator.js`
- `frontend/src/api/image.js`

这些文件共同构成商品详情图业务，但不在同一业务模块下。当前规模还能接受；如果继续增长，建议以业务域收敛二级结构，例如保留顶层技术目录的同时，把 composable 也按 `product-image`、`product-video`、`outfit` 子目录拆开。

`frontend/src/components/generation/` 放的是跨场景生成工作台组件，但里面同时有通用 shell、图片 uploader、图片卡片、视频卡片、编辑弹窗：

- `frontend/src/components/generation/workspace/GenerationWorkspace.vue`
- `frontend/src/components/generation/image/ImageUploader.vue`
- `frontend/src/components/generation/cards/GeneratedCardGrid.vue`
- `frontend/src/components/generation/cards/VideoGeneratedCardGrid.vue`
- `frontend/src/components/generation/image/ImageEditModal.vue`

已拆出 `components/generation/workspace/`、`components/generation/cards/` 和 `components/generation/image/`；后续新增生成工作台组件时应继续按职责放入这些子目录。

### 后端

后端顶层技术分层基本清楚：

- `backend/app/routers/`：FastAPI 路由
- `backend/app/core/`：领域逻辑、基础设施、provider、策略生成
- `backend/app/models/`：SQLAlchemy model
- `backend/app/schemas/`：全局 response schema
- `backend/app/services/`：任务入队/扣费事务 helper，以及图片生成任务编排
- `backend/app/worker/`：异步生成任务

主要问题是 routers 层承载了过多业务编排：

- `backend/app/routers/video.py` 同时包含视频策略生成、视频任务创建、任务状态查询、软删除、下载代理。比 `image.py` 窄一些，但同样把业务校验、扣费、prompt 构建、入队编排放在 router。
- `backend/app/routers/billing.py` 同时处理套餐读取、订单创建、支付网关调用、订单查询、异步通知回调、交易记录。支付 provider 编排建议下沉到 `services/billing.py` 或 `core/payment.py`。

`backend/app/core/` 职责也偏宽：既有 `database.py`、`deps.py`、`time.py` 这类基础设施，也有 `image_strategy_generation.py`、`generation_prompt_builder.py`、`product_catalog.py`、`video_strategy_generation.py` 这类业务域逻辑。建议后续继续把业务编排移入 `backend/app/services/`，`core` 保留基础能力和 provider 封装。

## 2. 命名一致性

### 文件名风格

当前风格基本符合语言习惯：

- Vue 组件：PascalCase，例如 `ProductImageView.vue`、`GenerationWorkspace.vue`
- 前端目录：kebab-case，例如 `product-image`、`product-video`、`free-image`
- composable：camelCase + `useXxx.js`，例如 `useProductImageGenerator.js`
- Python：snake_case，例如 `generation_prompt_builder.py`

### 同类文件命名模式

generator 场景 composable 命名一致：

- `frontend/src/composables/generator/useFreeImageGenerator.js`
- `frontend/src/composables/generator/useOutfitGenerator.js`
- `frontend/src/composables/generator/useProductImageGenerator.js`
- `frontend/src/composables/generator/useProductSuiteGenerator.js`
- `frontend/src/composables/generator/useProductVideoGenerator.js`

但这些文件实际都是页面级 orchestrator，不只是“generator”：它们通常会管理表单状态、策略生成、任务恢复、任务创建、卡片动作、历史任务。建议命名为 `useProductImageWorkspace.js` 或拆出子 composable：`useProductImageStrategy.js`、`useProductImageBatch.js`、`useProductImageRestore.js`。

### 前后端概念对齐

存在 `generation/job/task` 三套概念混用：

- 前端 API：`frontend/src/api/generation.js` 使用 `createGenerationJob`、`listGenerationJobs`
- 后端模型：`backend/app/models/generation_job.py` 使用 `GenerationJob`
- 图片/视频模型：`backend/app/models/image_task.py`、`backend/app/models/video_task.py`
- 页面文案和函数常用“任务”：`currentTaskTitle`、`historyTasks`、`createNewTask`

建议明确概念边界：`GenerationJob` 表示工作区/一次生成批次容器，`ImageTask`/`VideoTask` 表示单个媒体生成任务。前端变量可以改为 `currentJobTitle`、`historyJobs`，避免 UI 代码里 job/task 互换。

`scenario`、`type_id`、`module`、`structure` 也有轻微混用：

- 商品详情图前端叫 module：`selectedModules`、`StrategyModuleCard.vue`
- 后端接口统一用 `type_id` 和 `structure`
- 套图前端叫 structure：`SuiteStructureConfigurator.vue`
- 视频前端叫 type：`VideoTypeSelector.vue`

建议补一份短命名约定：场景用 `scenario`，业务子类型用 `typeId`，详情图模块用 `moduleId`，套图结构用 `structure`，不要在同一层接口里把 `type_id` 同时代表模块、视频方向、场景。

### 路由/函数命名是否诚实

`backend/app/routers/video.py` 命名较宽，实际同时包含视频策略生成、视频任务创建、状态查询、删除、下载代理。后续可按 `video_strategy.py`、`video_tasks.py`、`video_downloads.py` 拆成更诚实的 router/service 组合。

`backend/app/routers/generation.py` 名字像所有生成 API 的入口，但实际只管理 `GenerationJob` 容器。这个改名会影响前后端概念边界，建议确认 `job/task` 命名规则后再改为 `generation_jobs.py`。

`backend/app/core/generation_prompt_builder.py` 已聚焦图片生成 prompt 构建。后续如果图片 prompt 继续增长，可以按商品详情图、套图、穿搭继续拆分。

## 3. 目录嵌套深度与扁平度

前端最深的常规路径是 4 层业务嵌套：

- `frontend/src/views/generator/product-image/ProductImageView.vue`
- `frontend/src/views/generator/product-video/ProductVideoView.vue`
- `frontend/src/views/generator/product-suite/ProductSuiteView.vue`
- `frontend/src/views/generator/free-image/FreeImageView.vue`

这个深度可以接受，因为 `views/generator/<scenario>` 能直接表达路由归属。真正的问题不是过深，而是同一业务在 `views/components/composables/constants/api` 横向分散。

需要重点拆分的目录：

- `frontend/src/composables/generator/` 已按职责拆出 `batch/`、`strategy/`、`restore/`；剩余问题集中在各场景 `useXxxGenerator.js` 仍然偏大。
- `backend/app/core/` 有 18 个直接 `.py` 文件，还包含 `providers/`、`strategy/` 子目录。建议把业务文件移出 `core`，否则 `core` 既像基础设施层又像业务服务层。

单文件体量也暴露了目录没有承接复杂度：

- `backend/app/services/image_generation.py`：约 390 行
- `backend/app/worker/image_tasks.py`：约 210 行
- `backend/app/worker/video_tasks.py`：约 235 行
- `frontend/src/composables/generator/useOutfitGenerator.js`：约 720 行
- `frontend/src/composables/generator/useProductVideoGenerator.js`：约 600 行
- `frontend/src/composables/generator/useProductSuiteGenerator.js`：约 580 行
- `frontend/src/composables/generator/useProductImageGenerator.js`：约 580 行

建议优先把“大 orchestrator” 拆成按职责命名的小 composable/service，而不是继续在同级目录新增类似文件。

## 4. 新人可读性

仅凭目录结构，新人能较快猜到前端图片/视频页面：

- 图片详情图：`frontend/src/views/generator/product-image/ProductImageView.vue`
- 商品视频：`frontend/src/views/generator/product-video/ProductVideoView.vue`
- 穿搭图：`frontend/src/views/generator/outfit/OutfitView.vue`
- 自由生图：`frontend/src/views/generator/free-image/FreeImageView.vue`

但后端仍会更容易猜错：商品详情图、商品套图、穿搭图、自由生图共享 `backend/app/services/image_generation.py` 和图片策略/任务子路由，而不是各自有 `product_image.py`、`product_suite.py`、`free_image.py` service。

容易猜错的具体例子：

1. `backend/app/services/image_generation.py`
   能看出是图片生成主链路，但商品详情图、商品套图、穿搭图、自由生图的创建/重生编排都收在同一个 service。后续如果继续增长，可按场景拆成更小的 service。

2. `backend/app/routers/video.py`
   名字像视频资源入口，但实际同时负责策略生成、任务创建、状态查询、软删除和下载代理。建议后续拆成 `video_strategy.py`、`video_tasks.py`、`video_downloads.py`，业务编排下沉到 service。

3. `backend/app/routers/generation.py`
   名字像所有生成 API 的入口，但实际只管理 `GenerationJob` 容器；真正创建图片/视频任务在 `image.py` 和 `video.py`。建议改为 `generation_jobs.py`，前端 `api/generation.js` 也可改为 `api/generationJobs.js`。

## 建议优先级

P2：继续拆 `frontend/src/composables/generator/` 里的场景级大 composable，优先把各场景内部的恢复、策略生成、批量生成辅助函数继续下沉到已建立的职责目录。

P3：确认 `GenerationJob` 与 `ImageTask`/`VideoTask` 命名边界后，再考虑 `backend/app/routers/generation.py`、`frontend/src/api/generation.js` 的 job 化改名。
