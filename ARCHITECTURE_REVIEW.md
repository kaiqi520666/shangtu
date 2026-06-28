# ShangTu 架构债务清单（待办）

> 本文件原为 2026-06-28 的完整架构评审，现已瘦身为「仍未处理的技术债」清单。
> 已完成项的分析段落已删除，避免与当前代码不符。索引现状请用 CodeGraph 实时查询。

以下条目按严重程度排序。

## P0 / 高风险

## P1 / 中高风险

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


### 8. 启动时自动建表
- 位置：`backend/app/main.py:lifespan` 的 `Base.metadata.create_all`。
- 现状：与应用启动耦合，MVP 可接受。
- 建议：生产化前移到显式脚本/迁移命令（当前 MVP 规则允许破坏性 schema 变更，不必马上引入复杂迁移）。
