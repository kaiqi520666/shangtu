# ShangTu 架构债务清单（待办）

> 本文件原为 2026-06-28 的完整架构评审，现已瘦身为「仍未处理的技术债」清单。
> 已完成项的分析段落已删除，避免与当前代码不符。索引现状请用 CodeGraph 实时查询。

## 已落地的重构（上下文锚点，勿在此展开）

按当时评审第 8 节的顺序，以下抽象均已完成并逐行核对行为等价：

- `6fced73` 集中 Redis 任务状态：`backend/app/core/task_state.py`（key/TTL/状态合并）；前端 `frontend/src/utils/apiError.js`。
- `743a4a7` 任务创建/补偿服务：`backend/app/services/generation_tasks.py`（`deduct_credits_or_fail` / `enqueue_or_compensate`）。
- `7c18234` / `3b5fed9` 拆 Worker：`backend/app/core/providers/toapis_provider.py`（ToAPIS 协议）、`backend/app/core/generated_media_storage.py`（下载+上传 OSS）。
- `c179bf2` 媒体投影集中：`backend/app/core/media_projection.py`（image/video 的 select 与 payload）。

以下条目是上述工作**未覆盖**的部分，按严重程度排序。

## P0 / 高风险

### 1. Worker 失败处理与退款仍是图片/视频双写
- 位置：`backend/app/worker/tasks.py` 的 `_mark_failed`/`_mark_timeout`/`_mark_video_failed`/`_mark_video_timeout`、`refund_task_credit`/`refund_video_task_credit`、`update_task_in_db`/`update_video_task_in_db`、`_set_progress`/`_set_video_progress`、`fetch_task_user_id`/`fetch_video_task_user_id`。
- 现状：Redis 写入已统一走 `task_state.py`，但上面这些函数仍是「只有 model 和 media_type 前缀不同」的平行实现，重复度 >70%。
- 风险：新增媒体类型会继续复制一组；改失败语义/退款逻辑需同步图片和视频两处。
- 建议：抽 `TaskStateRepository`（参数化 model / media_type）+ `refund_generation_credit(task_model, task_id)`。

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

### 4. 前后端能力配置仍手动双写
- 位置：`backend/app/core/providers/toapis_provider.py:TOAPIS_SIZE_TABLE`、`frontend/src/constants/generator.js:resolutionMap`。
- 风险：一端新增比例/4K，另一端未同步 → 前端可选但后端失败，或反之。
- 建议：后端暴露 `/image/capabilities`，前端消费；尺寸表作为唯一来源。

### 5. 前端场景 composable 过大
- 位置：`frontend/src/composables/generator/useOutfitGenerator.js`（最重，兼管模特库 CRUD/上传/删除）、`useProductImageGenerator.js`、`useProductSuiteGenerator.js`、`useProductVideoGenerator.js`，均 500–700+ 行。
- 现状：已有通用 `frontend/src/composables/generator/useGenerationRunner.js`、`useGenerationCards.js`、`useGenerationStrategyFlow.js`，但场景层仍是「上帝 composable」。
- 风险：新增场景大概率复制 500+ 行结构，局部修改易破坏恢复/生成。
- 建议：先抽 `useOutfitModels()`，再抽 `cloneUploadedImages()`/`restoreCommonImageSettings()`/`validateUploadedMainImage()`/`buildImageSnapshotPayload()` 等轻量共享工具；不急着大框架化。

## P2 / 中风险

### 6. OSS 失败不可恢复 + 存储无中性接口
- 位置：`backend/app/core/generated_media_storage.py:materialize_to_oss/materialize_video_to_oss`、`backend/app/core/oss.py:OssConfigError` 与调用方。
- 现状：下载 provider 结果后上传 OSS，任一异常即任务失败 + 退款，用户无法复用已生成的 provider 结果重试上传；存储仍直接绑定 Aliyun `oss2`，异常名/语义泄漏到业务层。
- 建议：失败时至少记录 `provider_task_id` 和原始 `final_url`（短期存 error/context JSON）供后台补偿；新增中性 `StorageConfigError`/`upload_media_bytes()`，Aliyun OSS 作为默认实现。

### 7. 日志体系薄
- 位置：`backend/app/worker/tasks.py`（`print()` / `traceback.print_exc()`）。
- 风险：无法按 task_id / provider_task_id / media_type 聚合排查超时、上传失败、上游安全策略问题。
- 建议：引入标准 logging 配置，保证 task_id、media_type、provider_task_id 出现在结构化日志字段。

### 8. Redis 与 DB 双写无强一致保证
- 位置：worker 写 DB + Redis；router 经 `task_state.merge_task_state` 合并读取；`asset.batch_delete_assets` best effort 清 Redis。
- 现状：「先 DB 后 Redis」+ 合并读取已是正确补丁，但状态仍是双写，Redis 过期/丢失时短期状态可能不一致，前端轮询异常被吞掉只表现为卡住。
- 建议：以 DB 为最终状态源，Redis 仅作进度缓存；进度长时间不变时给出可见错误或加后台超时扫描。

### 9. 启动时自动建表
- 位置：`backend/app/main.py:lifespan` 的 `Base.metadata.create_all`。
- 现状：与应用启动耦合，MVP 可接受。
- 建议：生产化前移到显式脚本/迁移命令（当前 MVP 规则允许破坏性 schema 变更，不必马上引入复杂迁移）。
</content>
</invoke>
