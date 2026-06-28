# frontend/AGENTS.md

本文件只适用于 `frontend/` 目录。通用 MVP、Git、复用和不兼容旧逻辑的规则见仓库根目录 `AGENTS.md`。

## 技术栈

- Vue 3 + `<script setup>`
- Vite
- Tailwind CSS
- lucide-vue-next
- axios
- JavaScript only，不使用 TypeScript

## 常用命令

```bash
npm install
npm run dev
npm run build
```

## 前端规则

- 业务状态和副作用优先放 composable，组件保持薄。
- 通用请求放 `src/api/`，不要在多个页面重复写同一请求逻辑。
- 通用 UI 放 `src/components/ui/`，业务组件放对应业务目录。
- 生成工作台优先复用 `GenerationWorkspace`、`ImageUploader`、`GenerationHistoryDrawer`、`useGenerationRunner`、`useGenerationCards`、`useCardActions`。
- 不为视频/图片重复写两套相同的工作台逻辑；差异只放在真正不同的卡片、输入、接口适配或媒体预览层。
- AI 帮写统一走 `useAiSellingPointsWriter` 和 `src/utils/analyzeImages.js` 的带标签多图分析，不在场景 composable 里复制请求流程。
- 生成参数快照统一通过 `src/utils/generationSnapshots.js` 构造、读取和克隆，不在页面里手写多套 snapshot shape。
- 管理后台继续复用 `AdminLayoutView`、`AdminPagination`、`AppSelect`、`AppCheckbox`、`AppModal`、`GlobalConfirm`、`GlobalToast`。
- Pinia 只放跨业务全局状态；生成页和后台列表页的页面状态优先放 composable。

## 目录约定

- `src/api/`：统一封装请求函数。
- `src/composables/`：状态、副作用、生成流程和可复用业务逻辑。
- `src/composables/generator/`：生成工作台流程、卡片、任务恢复和场景生成器 composable。
- `src/composables/admin/`：管理后台列表和筛选状态。
- `src/components/ui/`：通用 UI 组件。
- `src/components/generation/`：生成工作台通用组件。
- `src/components/<module>/`：模块业务组件。
- `src/views/`：页面组装，不堆复杂业务逻辑。
- `src/constants/`：平台、尺寸、模式、展示选项等常量。
- `src/utils/`：纯工具函数。

## 验证

- 修改前端代码后至少运行 `npm run build`。
- 改动任务恢复、卡片展示或 snapshot 结构时，同步检查后端 payload。
- 不用 `npm run lint` 做普通验证；它会自动 `--fix` 并可能带入无关格式化改动。
