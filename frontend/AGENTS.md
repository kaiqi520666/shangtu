# frontend/AGENTS.md

本文件只适用于 `frontend/`。仓库根目录 `AGENTS.md` 中的 MVP、极简代码、复用、Git 和跨端同步规则继续生效。

## 技术栈与运行方式

- Vue 3 + `<script setup>` + Composition API，前端代码只使用 JavaScript。
- Vite 8、Vue Router、Pinia、Tailwind CSS v4、lucide-vue-next、axios。
- npm + `package-lock.json` 管理依赖；Node.js 版本以 `package.json#engines` 为准。
- Vitest + Vue Test Utils + jsdom 负责单元测试。
- 开发和预览环境由 Vite 将 `/api` 代理到本地后端；其他环境通过 `VITE_API_BASE_URL` 指定 API 地址。

## 常用命令

```bash
npm ci
npm run dev
npm run test
npm run build
npm run build:check
```

- 普通前端改动至少运行 `npm run build`；改到已有测试覆盖的逻辑时同时运行 `npm run test`。
- 影响首屏依赖或新增较大资源时运行 `npm run build:check`，确认 bundle 预算。
- `npm run lint` 和 `npm run format` 会修改文件，只在明确需要时运行，并在运行后检查 diff。

## 应用架构

- `src/main.js` 是启动入口，注册 Pinia、持久化插件和 Router，并在挂载前加载图片能力配置。
- `src/App.vue` 只承载全局布局、`RouterView`、充值弹窗、Toast 和 Confirm 等全局 UI。
- `src/router/index.js` 聚合 `src/router/routes/` 下的公共、生成器、账户和后台路由，并统一处理登录态和超级管理员权限。
- `src/api/request.js` 是唯一 axios 实例，负责 API base URL、Bearer token 和积分回写；业务请求按资源放在 `src/api/*.js`。
- `src/stores/` 只保存跨页面状态。目前认证和后端目录数据由 Pinia 管理；页面表单、轮询和弹窗状态不要放进 store。
- `src/views/` 是路由页面组装层；生成器页面应组合业务组件和场景 composable，不直接承载完整请求、轮询、恢复流程。

## 目录与职责边界

- `src/components/ui/`：无业务语义的基础 UI，以及全局 Toast、Confirm、Modal、Drawer、Select、Pagination 等组件。
- `src/components/generation/`：所有生成场景共享的工作台、上传、预览、卡片和历史任务组件。
- `src/components/<module>/`：商品图、套图、穿搭、视频、数字人、配音等模块专属组件。
- `src/components/admin/`：后台业务面板；页面壳留在 `src/views/admin/`。
- `src/composables/generator/`：场景生成器、卡片状态、任务恢复和公共批处理流程；子目录按 `batch/`、`restore/`、`strategy/` 分层。
- `src/composables/admin/`：后台分页、筛选、加载和编辑状态。
- `src/composables/<module>/`：模块内可复用的状态与副作用。
- `src/constants/`：场景、生成能力、平台和展示选项等固定配置。
- `src/utils/`：不依赖 Vue 响应式上下文的纯函数。

新文件应放入拥有该逻辑的最窄层级。只有两个以上模块共同使用的实现才上移到通用目录。

## 生成工作台约束

- 工作台壳、上传器、历史抽屉和结果卡片优先复用 `components/generation/` 的现有实现。
- 批量创建、任务轮询、历史加载和任务恢复优先扩展 `useMediaBatchRunner`、`useGenerationCards`、`useGeneratorRouteJob`，不要在场景页面重写一套。
- 卡片下载、选择和预览操作统一复用 `useCardActions`；图片编辑沿用现有卡片编辑流程。
- 商品图、商品套图和穿搭策略流程优先复用 `useGenerationStrategyFlow`，场景差异留在对应 `useXxxGenerator`。
- AI 卖点生成统一走 `useAiSellingPointsWriter` 和 `utils/analyzeImages.js`，不要在场景 composable 复制多图分析请求。
- 生成设置的构造、克隆和恢复统一走 `utils/generationSnapshots.js`。修改 snapshot shape 时同步修改后端 job/task payload、恢复逻辑和对应测试。
- `:jobId?` 路由是任务恢复入口。修改任务加载、排序、替换或归档语义时，检查所有图片、视频、数字人、视频翻译和配音场景。
- 所有轮询定时器、事件监听和延迟保存定时器都必须在组件卸载或切换任务时清理。

## API、状态与错误处理

- Vue 组件和 composable 只能调用 `src/api/` 导出的业务函数，不直接创建 axios 实例。
- API 返回值遵循后端 `{ code, message, data }`；网络错误文案优先使用 `utils/apiError.js`，业务失败使用后端 `message`。
- 认证 token 和用户积分由 `useAuthStore` 管理；请求成功后的积分同步由响应拦截器处理，不在页面重复写回。
- 后端目录数据由 `useCatalogStore` 统一加载和查询。目录管理变更后使用 reload 语义刷新，不在组件维护第二份全局目录缓存。
- 全局提示、确认和充值弹窗分别通过现有 composable 调用，不在页面重复挂载全局组件。

## UI 与测试

- 保持当前安静、工具型的工作台视觉；使用现有主题变量、Tailwind v4 和 lucide 图标，不引入第二套 UI 系统。
- 通用 UI 改动先检查 `src/components/ui/`；后台分页、选择、弹窗和确认交互必须复用已有组件。
- 页面只负责布局和模块编排。template 超过 150 行或 script 超过 200 行时按业务边界拆组件或 composable。
- 单元测试与源码同目录，命名为 `*.test.js`。纯状态逻辑优先测 composable/utils，关键交互使用 Vue Test Utils 测组件。
- 修改 API payload、任务状态、生成快照或媒体资产结构时，除前端测试外必须同步核对后端 model、router、service 和 worker 输出。
