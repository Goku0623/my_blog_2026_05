# 博客系统前端

基于 Vite + Vue3 + TypeScript + Tailwind CSS 4，模块化架构。

## 快速开始

```bash
npm install
npm run dev     # http://127.0.0.1:5173
npm run build
```

## 项目结构

```
src/
├── api/            # API 封装（Axios + 拦截器 + 类型定义）
├── stores/         # Pinia（auth/guest/site）
├── composables/    # 组合式工具（useMarkdown）
├── modules/
│   ├── blog/       # 博客前台（首页/文章/分类/标签/留言/关于/AI助手）
│   └── admin/      # 管理后台（仪表盘/文章/评论/留言/统计/系统/通知）
├── ui/             # 自研组件（Modal/Input/Button/Avatar/Toast等）
├── router/         # Vue Router（懒加载，admin 路由守卫）
└── utils/          # 工具函数（时间格式化）
```

## 核心特性

- Pinia 状态管理（auth token 自动刷新、游客身份持久化）
- Axios 拦截器（自动注入 Bearer、401 自动刷新重试）
- markdown-it + highlight.js 渲染
- 暗色/亮色主题切换
- 管理端顶部通知铃铛（未读计数、30 秒轮询、一键已读）
- AI 助手面板（N8N Webhook 驱动，游客日限额，管理员不限额）
