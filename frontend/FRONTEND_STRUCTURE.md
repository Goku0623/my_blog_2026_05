# Frontend 项目结构说明

## 目录结构

```
frontend/src/
├── api/                    # Axios 请求封装
│   ├── index.ts            # Axios 实例（baseURL、拦截器、token 注入、401自动刷新）
│   ├── auth.ts             # 管理员认证相关 API
│   ├── articles.ts         # 文章管理 API
│   ├── comments.ts         # 评论管理 API
│   ├── ai.ts               # AI（天气、评论回复建议等）API
│   ├── system.ts           # 系统配置 API
│   ├── statistics.ts       # 数据统计 API
│
├── ui/                     # 自研组件（Button、Card、Modal、Toast、Pagination 等）
│
├── modules/
│   ├── blog/               # 博客前台（游客视角）
│   │   ├── views/
│   │   │   ├── HomeView.vue        # 文章列表
│   │   │   ├── ArticleView.vue     # 文章详情（含评论）
│   │   │   ├── CategoryView.vue    # 分类页
│   │   │   └── SearchView.vue      # 搜索结果页
│   │   └── components/
│   │       ├── ArticleCard.vue     # 文章卡片
│   │       ├── CommentSection.vue  # 评论区
│   │       ├── CommentItem.vue     # 单条评论
│   │       └── SiteFooter.vue / SiteNavbar.vue  # 页脚 / 导航
│   │
│   └── admin/              # 管理后台
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── DashboardView.vue
│       │   ├── ArticlesView.vue
│       │   ├── ArticleEditorView.vue  # Markdown 编辑器
│       │   ├── CommentsView.vue
│       │   ├── SystemConfigView.vue
│       │   ├── SensitiveWordsView.vue
│       │   ├── OperationLogsView.vue
│       │   └── StatisticsView.vue     # ECharts 图表
│       └── components/
│           ├── StatCard.vue           # 仪表盘统计卡
│           └── HealthRow.vue          # 健康检查行
│
├── stores/
│   ├── auth.ts             # Pinia：管理员登录状态
│   ├── guest.ts            # Pinia：游客身份（guest_token 持久化到 localStorage）
│   └── site.ts             # Pinia：站点公共配置
│
├── router/
│   └── index.ts            # Vue Router（懒加载，admin 路由需要 auth guard）
│
├── composables/
│   └── useMarkdown.ts      # markdown-it + highlight.js 渲染
│
├── utils/
│   └── time.ts             # 时间格式化
│
├── style.css               # 全局样式（Tailwind 4、主题变量）
│
└── main.ts                 # 入口：Pinia、Router、全局 confirm、主题初始化
```

## 核心功能实现说明

### 1. Axios 请求拦截器 (`src/api/index.ts`)

**功能特性：**
- 自动注入 Bearer token（管理员认证）
- 自动注入 X-Guest-Token（游客身份）
- 401 错误自动刷新 token 并重试
- 刷新 token 失败自动跳转登录页
- 请求队列管理（避免并发刷新）

**关键实现：**
```typescript
// 请求拦截器：注入 token
config.headers.Authorization = `Bearer ${authStore.token}`
config.headers['X-Guest-Token'] = guestStore.guestToken

// 响应拦截器：401 自动刷新
if (error.response?.status === 401) {
  await refreshToken()
  return request(originalRequest) // 重试
}
```

### 2. 路由守卫 (`src/router/index.ts`)

**功能特性：**
- 管理后台路由懒加载
- beforeEach 守卫验证登录状态
- 未登录自动跳转登录页
- 已登录访问登录页自动跳转仪表盘

**路由配置：**
```typescript
// 前台路由
/ -> HomeView (文章列表)
/article/:slug -> ArticleView (文章详情)
/category/:id -> CategoryView (分类)
/search -> SearchView (搜索)

// 管理后台路由（需要登录）
/admin/login -> LoginView
/admin/dashboard -> DashboardView
/admin/articles -> ArticlesView
/admin/articles/new -> ArticleEditorView
/admin/articles/edit/:id -> ArticleEditorView
... 其他管理页面
```

### 3. Pinia Store

#### authStore (`src/stores/auth.ts`)
- 管理员登录状态管理
- token 持久化到 localStorage
- 自动刷新 token
- 登出清空所有状态

#### guestStore (`src/stores/guest.ts`)
- 游客身份管理
- 首次访问自动获取 guest_token
- guest_token 持久化到 localStorage

#### siteStore (`src/stores/site.ts`)
- 站点公共配置（站点名称、描述等）
- 全局配置管理

### 4. Markdown 渲染 (`src/composables/useMarkdown.ts`)

**功能特性：**
- markdown-it 渲染
- highlight.js 代码高亮
- HTML 安全处理

**使用示例：**
```typescript
const { render } = useMarkdown()
const html = render('# Hello World')
```

## Vite 配置 (`vite.config.ts`)

**关键配置：**
```typescript
// 路径别名
alias: {
  '@': resolve(__dirname, 'src'),
}

// 代理（目标以本机后端为准，见 vite.config.ts）
proxy: {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    ws: true,
  },
  '/ws': {
    target: 'ws://127.0.0.1:8000',
    ws: true,
    changeOrigin: true,
  },
}

// 代码分割（manualChunks 函数，节选）
manualChunks(id) {
  if (!id.includes('node_modules')) return
  if (id.includes('echarts') || id.includes('vue-echarts')) return 'echarts'
  if (id.includes('markdown-it') || id.includes('highlight.js')) return 'markdown'
  if (id.includes('lucide-vue-next')) return 'icons'
}
```

插件示例：`plugins: [vue(), tailwindcss()]`

## 运行项目

### 开发环境
```bash
cd frontend
npm install
npm run dev
```

访问：http://127.0.0.1:5173（或 http://localhost:5173，与 `package.json` 中 dev 脚本一致）

### 生产构建
```bash
npm run build
npm run preview
```

## 技术栈

- **框架：** Vue 3 + TypeScript + Vite
- **样式：** Tailwind CSS 4（`@tailwindcss/vite`）
- **组件：** `src/ui` 自研业务组件 + Tailwind 实用类
- **图标：** lucide-vue-next
- **状态管理：** Pinia
- **路由：** Vue Router 4
- **HTTP：** Axios
- **Markdown：** markdown-it + highlight.js
- **图表：** ECharts + vue-echarts
- **组合式工具：** @vueuse/core
- **实时能力（可选）：** 后端可提供 WebSocket（如管理端评论通知）；开发环境经 Vite `/ws` 代理转发

## 待完成功能（TODO）

- [ ] 可选：抽取 `TagCloud.vue` 等小组件以复用样式
- [ ] 文章编辑器：预览、素材上传、快捷键
- [ ] 数据统计与管理视图：图表与导出等增强

## 注意事项

1. **token 管理：** 
   - 管理员 token 存储在 localStorage（key: `admin_token`、`admin_refresh_token`）
   - 游客 token 存储在 localStorage（key: `guest_token`）

2. **API 接口：** 
   - 所有 API 请求都通过 `/api` 代理到后端
   - 如需 WebSocket，可通过 `/ws` 代理到后端

3. **路由守卫：** 
   - 所有 `/admin/*` 路由都需要登录
   - 未登录访问管理后台会自动跳转登录页

4. **TypeScript：** 
   - 所有 API 接口都有完整的类型定义
   - 使用 `type` 导入 Axios 类型避免编译错误
