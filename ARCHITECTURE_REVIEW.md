# ShangTu 架构债务清单（待办）

> 本文件原为 2026-06-28 的完整架构评审，现已瘦身为「仍未处理的技术债」清单。
> 已完成项的分析段落已删除，避免与当前代码不符。索引现状请用 CodeGraph 实时查询。

以下条目按严重程度排序。

## P0 / 高风险

### 1. Worker 图片/视频主编排仍平行实现
- 位置：`backend/app/worker/image_tasks.py:generate_image`、`backend/app/worker/video_tasks.py:generate_video`、`backend/app/worker/image_tasks.py:_set_progress`、`backend/app/worker/video_tasks.py:_set_video_progress`。
- 现状：失败归一化已迁到 `backend/app/worker/task_failures.py`，DB/退款同步已迁到 `backend/app/worker/task_state_sync.py`，但图片/视频任务的 provider 创建、轮询、进度写入、结果落 OSS 仍是两套相似编排。
- 风险：新增媒体类型会继续复制一条完整 worker 流程；轮询/进度/最终落库语义修改时仍要同步图片和视频两处。
- 建议：抽 `run_generation_task(media_type, config, payload_builder)` 之类的轻量 runner，保留图片/视频差异在 payload、等待时间、错误文案和存储函数配置里。

## P1 / 中高风险

### 2. 后端无统一异常处理
- 位置：`backend/app/schemas/response.py:fail` + 各 router 局部 `except Exception`。
- 风险：未捕获异常走 FastAPI 默认 500，与 `Response` envelope 不一致；前端 fallback 文案不稳定，线上排查困难。
- 建议：加 FastAPI 全局 exception handler，把未知异常统一转成 `Response(code=1)` 并记录日志；业务异常保留局部处理。

### 3. Provider 接口未正式化
- 位置：`backend/app/core/providers/toapis_provider.py`、`backend/app/core/model_config.py`。
- 现状：ToAPIS 协议已集中，但仍是一组 ToAPIS 专用函数，不是可替换接口；`model_config.py` 只有模型名，没有 provider 能力元数据。
- 风险：接第二个图片/视频供应商时仍要在 worker 里加分支，而不是新增一个 adapter 实现。
- 建议：定义 `ImageGenerationProvider` / `VideoGenerationProvider` 接口（`create` / `poll` / `extract_result` / `supported_sizes`），ToAPIS 作为默认实现。

### 5. 前端场景 composable 过大
- 位置：`frontend/src/composables/generator/useOutfitGenerator.js`（最重，兼管模特库 CRUD/上传/删除）、`useProductImageGenerator.js`、`useProductSuiteGenerator.js`、`useProductVideoGenerator.js`，均 500–700+ 行。
- 现状：已有通用 `frontend/src/composables/generator/batch/useMediaBatchRunner.js`、`frontend/src/composables/generator/useGenerationCards.js`、`frontend/src/composables/generator/strategy/useGenerationStrategyFlow.js`，但场景层仍是「上帝 composable」。
- 风险：新增场景大概率复制 500+ 行结构，局部修改易破坏恢复/生成。
- 建议：先抽 `useOutfitModels()`，再抽 `cloneUploadedImages()`/`restoreCommonImageSettings()`/`validateUploadedMainImage()`/`buildImageSnapshotPayload()` 等轻量共享工具；不急着大框架化。

## P2 / 中风险

### 6. OSS 失败不可恢复 + 存储无中性接口
- 位置：`backend/app/core/generated_media_storage.py:materialize_to_oss/materialize_video_to_oss`、`backend/app/core/oss.py:OssConfigError` 与调用方。
- 现状：下载 provider 结果后上传 OSS，任一异常即任务失败 + 退款，用户无法复用已生成的 provider 结果重试上传；存储仍直接绑定 Aliyun `oss2`，异常名/语义泄漏到业务层。
- 建议：失败时至少记录 `provider_task_id` 和原始 `final_url`（短期存 error/context JSON）供后台补偿；新增中性 `StorageConfigError`/`upload_media_bytes()`，Aliyun OSS 作为默认实现。


### 7. Redis 与 DB 双写无强一致保证
- 位置：`backend/app/worker/image_tasks.py` / `backend/app/worker/video_tasks.py` 写 DB + Redis；router 经 `backend/app/core/task_state.py:merge_task_state` 合并读取；`backend/app/routers/asset.py:batch_delete_assets` best effort 清 Redis。
- 现状：「先 DB 后 Redis」+ 合并读取已是正确补丁，但状态仍是双写，Redis 过期/丢失时短期状态可能不一致，前端轮询异常被吞掉只表现为卡住。
- 建议：以 DB 为最终状态源，Redis 仅作进度缓存；进度长时间不变时给出可见错误或加后台超时扫描。

### 8. 启动时自动建表
- 位置：`backend/app/main.py:lifespan` 的 `Base.metadata.create_all`。
- 现状：与应用启动耦合，MVP 可接受。
- 建议：生产化前移到显式脚本/迁移命令（当前 MVP 规则允许破坏性 schema 变更，不必马上引入复杂迁移）。
