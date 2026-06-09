# kaiqi-vue-template

一个轻量的 Vue 3 前端项目模板，适合作为 GitHub Template 快速创建新项目。

## 技术栈

- Vue 3
- Vite
- Vue Router
- Pinia
- Tailwind CSS v4
- lucide-vue-next
- ESLint
- oxlint
- oxfmt

## 环境要求

建议使用 Node.js：

```sh
^20.19.0 || >=22.12.0
```

当前模板使用 npm 和 `package-lock.json` 管理依赖。

## 快速开始

安装依赖：

```sh
npm install
```

启动开发服务：

```sh
npm run dev
```

生产构建：

```sh
npm run build
```

本地预览构建产物：

```sh
npm run preview
```

代码检查：

```sh
npm run lint
```

格式化源码：

```sh
npm run format
```

## 目录结构

```text
.
├── public/              # 静态资源
├── .github/
│   └── workflows/       # GitHub Actions
├── src/
│   ├── api/             # 接口请求与 axios 实例
│   ├── assets/          # 样式与资源
│   ├── components/      # 通用组件
│   │   ├── common/      # 业务无关基础组件
│   │   └── layout/      # 布局相关组件
│   ├── composables/     # Composition API 复用逻辑
│   ├── constants/       # 常量、枚举、固定配置
│   ├── directives/      # Vue 自定义指令
│   ├── layouts/         # 页面布局壳
│   ├── router/          # Vue Router 配置
│   ├── styles/          # 样式分层文件
│   ├── stores/          # Pinia store
│   ├── utils/           # 纯工具函数
│   ├── views/           # 页面组件
│   ├── App.vue          # 应用根组件
│   └── main.js          # 应用入口
├── AGENT.md             # Codex / AI Agent 项目工作规范
├── eslint.config.js     # ESLint 配置
├── vite.config.js       # Vite 配置
└── package.json
```

## 目录约定

- `views/` 只放页面级组件。
- `layouts/` 放页面布局壳，例如 `DefaultLayout.vue`。
- `components/common/` 放业务无关的通用组件。
- `components/layout/` 放导航、页头、页脚、页面容器等布局组件。
- `api/` 放接口模块和请求实例，不在页面组件中散写 axios 配置。
- `stores/` 只放跨页面共享状态。
- `composables/` 放 `useXxx.js` 形式的组合式函数。
- `constants/` 放常量、枚举和固定配置，避免魔法字符串。
- `utils/` 放纯工具函数，不依赖 Vue 响应式上下文。
- `directives/` 放 Vue 自定义指令。

## 路径别名

项目已配置 `@` 指向 `src`：

```js
import HomeView from '@/views/HomeView.vue'
```

## 样式

项目使用 Tailwind CSS v4，入口样式文件为：

```text
src/assets/main.css
```

当前通过 `@tailwindcss/vite` 接入 Vite。

## 环境变量

模板提供 `.env.example`：

```sh
VITE_APP_TITLE=kaiqi-vue-template
VITE_API_BASE_URL=/api
```

创建真实环境变量文件时，可以复制为 `.env` 或 `.env.local`。真实环境变量文件不会被 Git 提交。

## 请求封装

项目提供轻量 axios 实例：

```text
src/api/request.js
```

默认读取 `VITE_API_BASE_URL`，并在响应拦截器中返回 `response.data`。具体业务接口建议按模块继续放在 `src/api/` 下。

## 状态管理

项目默认接入 Pinia，并安装了 `pinia-plugin-persistedstate`。

使用持久化时请注意：

- 不要持久化 token、密码、密钥等敏感信息。
- 只持久化真正需要跨刷新保留的状态。
- 业务局部状态优先放在组件内部，不要全部放进全局 store。

## 模板使用建议

从该模板创建新项目后，建议先修改：

- `package.json` 中的 `name`、`description`、`repository`、`license`
- `index.html` 中的页面标题和基础 meta 信息
- `public/favicon.ico`
- `src/views/HomeView.vue` 中的首页内容
- README 中的项目名称和业务说明

如果项目需要环境变量，建议新增 `.env.example`，不要提交真实 `.env` 文件。

## 推荐 IDE

推荐使用 VS Code，并安装以下扩展：

- Vue - Official
- ESLint
- EditorConfig for VS Code
- Oxc

项目已提供 `.vscode/extensions.json` 推荐配置。

## CI

项目已提供 GitHub Actions：

```text
.github/workflows/ci.yml
```

默认在 `main` 分支 push 和 pull request 时执行：

```sh
npm ci
npm run lint
npm run build
```

## GitHub Template 发布前检查

发布为模板前建议确认：

- `npm run lint` 通过
- `npm run build` 通过
- `node_modules`、`dist`、日志文件和本地环境变量没有被提交
- README 已替换为当前模板说明
- 示例页面中没有未注册组件或强业务代码
- GitHub Actions 配置符合目标分支名称
