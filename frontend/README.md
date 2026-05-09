# 博客系统前端项目

基于 **Vite + Vue3 + TypeScript** 的个人博客系统前端，采用模块化架构设计。

## 快速开始

### 安装依赖
```bash
npm install
```

### 开发环境运行
```bash
npm run dev
```

开发服务器默认监听 **127.0.0.1:5173**（见 `package.json` 中 `npm run dev`）。浏览器可使用 http://127.0.0.1:5173 或 http://localhost:5173。

### 生产构建
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 项目特性

### ✅ 已完成的核心功能

1. **完整的 API 层封装**
   - Axios 拦截器自动注入 token
   - 401 错误自动刷新 token 并重试
   - 完整的类型定义

2. **Pinia 状态管理**
   - 管理员认证状态（authStore）
   - 游客身份管理（guestStore）
   - 站点配置管理（siteStore）
   - `auth` / `guest` 相关字段持久化到 **localStorage**；`site` 配置由接口加载后保存在内存（刷新后重新拉取）

3. **Vue Router 路由配置**
   - 前台路由（首页、文章详情、分类、搜索）
   - 管理后台路由（仪表盘、文章管理、评论管理等）
   - 路由懒加载优化
   - 完整的路由守卫（登录验证）

4. **Markdown 渲染**
   - markdown-it + highlight.js
   - 代码高亮支持

5. **工具函数库**
   - 完整的时间格式化函数
   - 相对时间显示（刚刚、5分钟前等）

### 📂 目录结构

```
src/
├── api/                    # API 请求封装（与后端 /api/v1 对应）
├── modules/
│   ├── blog/              # 博客前台（游客视角）
│   └── admin/             # 管理后台
├── ui/                    # 自研轻量组件（Button、Modal、Toast 等）
├── stores/                # Pinia 状态管理
├── router/                # Vue Router 配置
├── composables/           # 组合式函数（如 Markdown）
├── utils/                 # 工具函数
├── style.css              # 全局样式（Tailwind CSS 4 + CSS 变量主题）
└── main.ts               # 入口（Pinia、Router、全局 confirm）
```

详细结构说明请查看 [FRONTEND_STRUCTURE.md](./FRONTEND_STRUCTURE.md)

## 技术栈

实际依赖以 [`package.json`](./package.json) 为准，概要如下：

| 技术 | 版本（约） | 用途 |
|------|------------|------|
| Vue | 3.5+ | 前端框架（组合式 API） |
| TypeScript | 6.0+ | 类型系统 |
| Vite | 8.0+ | 开发与构建 |
| Tailwind CSS | 4.2+ | 原子化样式（`@tailwindcss/vite`） |
| Pinia | 3.0+ | 状态管理 |
| Vue Router | 4.6+ | 路由 |
| Axios | 1.16+ | HTTP 客户端 |
| @vueuse/core | 14.x | 组合式工具库 |
| lucide-vue-next | 0.47+ | 图标 |
| markdown-it + highlight.js | 14.x / 11.x | Markdown 与代码高亮 |
| ECharts + vue-echarts | 6.x / 8.x | 管理端图表 |

插件：`@vitejs/plugin-vue`、`@tailwindcss/vite`；路径别名 `@` → `src`（见 `vite.config.ts`）。

### Vite 与代理（摘录）

```typescript
server: {
  port: 5173,
  proxy: {
    '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, ws: true },
    '/ws': { target: 'ws://127.0.0.1:8000', ws: true, changeOrigin: true },
  },
},
build: {
  rollupOptions: {
    output: {
      manualChunks(id) {
        if (!id.includes('node_modules')) return
        if (id.includes('echarts') || id.includes('vue-echarts')) return 'echarts'
        if (id.includes('markdown-it') || id.includes('highlight.js')) return 'markdown'
        if (id.includes('lucide-vue-next')) return 'icons'
      },
    },
  },
}
```

开发命令在 `package.json` 中为 `vite --host 127.0.0.1 --port 5173 --strictPort`，浏览器可使用 http://127.0.0.1:5173 或 http://localhost:5173 访问。

生产环境由 **Nginx**（或同类网关）将 `/api`、`/ws` 反代至后端；静态资源由构建产物 `dist/` 托管。

## API 模块

| 模块 | 文件 | 功能 |
|------|------|------|
| Axios 实例 | `api/index.ts` | 拦截器、token 注入、401 自动刷新 |
| 认证 | `api/auth.ts` | 登录、登出、刷新 token |
| 文章 | `api/articles.ts` | 文章 CRUD、分类、标签 |
| 评论 | `api/comments.ts` | 评论 CRUD、审核 |
| AI | `api/ai.ts` | 天气查询、管理端评论 AI 回复建议 |
| 系统 | `api/system.ts` | 系统配置、敏感词、日志 |
| 统计 | `api/statistics.ts` | 仪表盘数据、访问统计 |

## 路由说明

### 前台路由（无需登录）
- `/` - 首页（文章列表）
- `/article/:slug` - 文章详情
- `/category/:id` - 分类页
- `/search` - 搜索

### 管理后台路由（需要登录）
- `/admin/login` - 管理员登录
- `/admin/dashboard` - 仪表盘
- `/admin/articles` - 文章管理
- `/admin/articles/new` - 新建文章
- `/admin/articles/edit/:id` - 编辑文章
- `/admin/comments` - 评论管理
- `/admin/system-config` - 系统配置
- `/admin/sensitive-words` - 敏感词管理
- `/admin/operation-logs` - 操作日志
- `/admin/statistics` - 数据统计

## 状态管理

### authStore（管理员认证）
```typescript
const authStore = useAuthStore()

// 登录
await authStore.login({ username, password })

// 登出
await authStore.logout()

// 获取当前用户信息
const user = authStore.adminInfo

// 检查登录状态
const isLoggedIn = authStore.isAuthenticated
```

### guestStore（游客身份）
```typescript
const guestStore = useGuestStore()

// 初始化游客身份（首次访问自动调用）
await guestStore.initGuest()

// 获取游客 token
const token = guestStore.guestToken

// 更新游客昵称
await guestStore.updateGuestName('新昵称')
```

### siteStore（站点配置）
```typescript
const siteStore = useSiteStore()

// 获取站点配置
await siteStore.fetchSiteConfig()

// 访问配置
const siteName = siteStore.config.site_name
```

## 常用 Composables

### useMarkdown（Markdown 渲染）
```typescript
const { render } = useMarkdown()

// 渲染 Markdown
const html = render('# Hello World\n\n```js\nconsole.log("Hello")\n```')
```

## 开发规范

### 文件命名
- 组件：大驼峰命名（`ArticleCard.vue`）
- API 模块：小驼峰命名（`articles.ts`）
- Store：小驼峰命名（`auth.ts`）
- Composables：小驼峰命名，以 `use` 开头（如 `useMarkdown.ts`）

### 代码风格
- 使用 TypeScript 严格模式
- 所有 API 接口都有类型定义
- 使用 `<script setup>` 语法
- 组件使用组合式 API

### 类型导入
```typescript
// ✅ 正确：使用 type 导入类型
import { type AxiosRequestConfig } from 'axios'

// ❌ 错误：直接导入类型
import { AxiosRequestConfig } from 'axios'
```

## 界面与组件

- **无重量级 UI 套件**：业务页面使用 **`src/ui`** 下自研组件（如 `UButton`、`UModal`、`toast` 等）与 **Tailwind** 实用类组合搭建。
- **图标**：`lucide-vue-next`。

## 待完成功能

- [ ] 文章编辑器增强（实时预览、图片上传与资源管理）
- [ ] 更完善的自动化测试（单元 / E2E）
- [ ] 可访问性、SEO 与管理端报表体验持续优化

（博客与管理端主流程已可用；细节以代码为准。）

## 注意事项

1. **Token 管理**
   - 管理员 token：`admin_token`、`admin_refresh_token`
   - 游客 token：`guest_token`
   - 所有 token 都存储在 localStorage

2. **代理配置**
   - 开发环境通过 Vite proxy 代理后端 API
   - 生产环境需要配置 Nginx 或其他反向代理

3. **路由守卫**
   - 所有 `/admin/*` 路由都需要登录
   - 未登录自动跳转到 `/admin/login`

4. **WebSocket（可选）**
   - 后端可为管理端等提供 WebSocket（如评论通知）；开发环境可通过 Vite `proxy` 转发 `/ws`

## License

MIT
