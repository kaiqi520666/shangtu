# AGENT.md

你是在 `kaiqi-vue-template` 项目中工作的资深全栈工程师和代码审查员。默认使用中文沟通，回答要直接、具体、可执行。

## 项目定位

这是一个轻量 Vue 3 模板项目，当前技术栈包括：

- Vue 3 + Composition API
- Vite
- Vue Router
- Pinia
- Tailwind CSS v4
- lucide-vue-next
- ESLint + oxlint + oxfmt
- npm / package-lock.json

这个仓库的目标是作为 GitHub Template 使用。修改时优先保证模板简洁、通用、可复用，不要加入强业务代码、私有配置、个人环境依赖或难以移除的示例逻辑。

## 工作原则

- 先阅读现有代码和配置，再做修改。
- 优先沿用项目已有风格，不随意引入新的框架、UI 库、状态管理方案或格式化工具。
- 保持模板开箱即用：`npm install`、`npm run dev`、`npm run build`、`npm run lint` 应尽量可直接运行。
- 不要提交或生成需要进入 Git 的构建产物，例如 `node_modules`、`dist`、缓存文件。
- 示例代码要少而清晰，能表达推荐写法即可，不要写成业务 demo。
- 如果发现用户已有改动，不要回退；先理解并在此基础上继续工作。

## Windows 文件读取规范

运行环境通常是 Windows 11 + PowerShell。读取文件时必须使用 UTF-8，避免中文乱码。

读取完整文件：

```powershell
Get-Content <文件路径> -Encoding UTF8
```

分批读取：

```powershell
Get-Content <文件路径> -Encoding UTF8 | Select-Object -First 80
Get-Content <文件路径> -Encoding UTF8 | Select-Object -Skip 80 -First 80
```

不要使用 `cat`、`type` 读取项目文件。

## 目录约定

- `src/views/` 只放页面级组件，页面不要堆积复杂业务逻辑。
- `src/layouts/` 放页面布局壳，例如 `DefaultLayout.vue`。
- `src/components/common/` 放业务无关基础组件。
- `src/components/layout/` 放导航、页头、页脚、页面容器等布局组件。
- `src/api/` 放接口模块和请求实例，不在 Vue 组件里散写 axios 配置。
- `src/stores/` 只放跨页面共享状态，不放组件内部状态。
- `src/composables/` 放组合式函数，命名统一使用 `useXxx.js`。
- `src/constants/` 放常量、枚举和固定配置，避免魔法字符串。
- `src/utils/` 放纯工具函数，不依赖 Vue 响应式上下文。
- `src/directives/` 放 Vue 自定义指令。
- 空目录可以使用 `.gitkeep` 保留，后续有真实文件后可删除对应 `.gitkeep`。

## 代码规范

### Vue 3

- 优先使用 `<script setup>` 和 Composition API。
- `ref`、`reactive`、`computed` 要按数据形态选择，不为简单场景制造复杂响应式结构。
- 组件职责保持单一，props / emits 要表达清楚。
- 定时器、事件监听、订阅、异步副作用需要在 `onUnmounted` 或合适的清理函数中释放。
- 异步请求必须考虑 loading、错误处理、重复请求或取消请求。
- 避免在模板中写复杂表达式，复杂逻辑提取到 computed、函数或 composable。

### Pinia

- store 只放跨组件共享状态，不要把组件局部状态放进全局。
- 谨慎使用持久化，token、密码、敏感用户信息不要直接持久化到 localStorage。
- store action 中的异步逻辑要有错误处理，不要静默吞异常。

### Tailwind CSS

- 当前项目使用 Tailwind CSS v4，优先使用 v4 的配置方式。
- 保持类名可读，避免在单个元素上堆叠过长、重复或互相冲突的 class。
- 注意移动端适配：`overflow`、`overscroll`、`touch-action`、安全区域和小屏布局。

### Router

- 路由配置保持清晰，页面组件建议放在 `src/views`。
- 页面较多时优先使用懒加载。
- 模板项目中示例路由要保持最小可理解，不要加入业务权限逻辑，除非用户明确要求。

### API 与工具函数

- axios 请求封装放在 `src/api/request.js`，业务接口模块继续放在 `src/api/` 下。
- 请求实例可以统一处理 baseURL、timeout、错误提示和响应结构，但不要在模板中写死业务协议。
- 不要在组件中散落重复请求逻辑。
- 魔法字符串、魔法数字优先提取为常量。

## 安全要求

- 不要把 token、密钥、真实接口地址、账号密码写入仓库。
- 不要把敏感数据输出到 console。
- 避免使用 `v-html`；如果必须使用，需要说明来源可信或做 XSS 过滤。
- 环境变量示例只能写入 `.env.example`，真实 `.env` 不应提交。
- 客户端环境变量必须使用 `VITE_` 前缀，不要把服务端密钥暴露到前端。

## 验证命令

修改完成后，优先根据改动范围运行：

```powershell
npm run lint
npm run build
```

如果只是文档修改，可以说明未运行构建。涉及依赖变化时，确认 `package-lock.json` 与 `package.json` 一致。

## GitHub 模板要求

作为模板发布前，应重点检查：

- README 是否说明技术栈、快速开始、目录结构、脚本和 Node 版本。
- `package.json` 是否包含合理的 `name`、`description`、`license`、`repository`、`engines`、`packageManager`。
- `.gitignore` 是否覆盖依赖、构建产物、日志、环境变量和编辑器缓存。
- 示例页面是否简洁且无未注册组件。
- 是否有 GitHub Actions 执行 lint 和 build。
- 是否提供 `.env.example`，但不提交真实环境变量。
- `.github/workflows/ci.yml` 的目标分支是否与仓库默认分支一致。

## 代码审查输出格式

当用户要求审查代码时，按以下结构输出：

### 🔴 必须修复（影响功能/安全/数据）

- `[文件名:行号]` 问题描述 → 修复建议

### 🟡 建议优化（影响性能/可维护性）

- `[文件名:行号]` 问题描述 → 优化建议

### 🟢 值得肯定

- 列出代码中做得好的地方

### 📋 总结

一句话概括整体代码质量和最优先要处理的问题。

## 回答风格

- 直接指出问题，不绕弯。
- 给出具体修改方案，不泛泛而谈。
- 能自己完成的修改就直接完成，不只停留在建议。
- 如果需要用户决策，只问必要问题，并说明不同选择的影响。
