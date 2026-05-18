# 个人博客

基于 FastAPI + Vue3 的全栈博客系统。

## 技术栈

**后端**: FastAPI / Tortoise ORM / PostgreSQL / Redis / Celery / WebSocket  
**前端**: Vue 3 + TypeScript / Vite / Tailwind CSS 4 / Pinia / Axios  
**部署**: Docker / Nginx

## 项目结构

```
├── backend/           # 后端（FastAPI）
│   ├── app/modules/   # 业务模块（auth/articles/comments/guestbook/ai/assistant/system/statistics）
│   ├── app/tasks/     # Celery 异步任务
│   ├── migrations/    # 数据库迁移
│   └── tests/
├── frontend/          # 前端（Vue3）
└── nginx/             # Nginx 配置
```

## 快速开始

### 环境要求

Python 3.13+ / PostgreSQL 16+ / Redis 7+ / Node.js 20+ / uv

### 后端

```bash
cd backend
cp .env.example .env   # 编辑配置数据库和 Redis
uv sync
uv run aerich upgrade   # 执行数据库迁移
uv run python create_admin.py  # 创建管理员（admin / admin123456）
uv run uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173，后端 API 文档 http://localhost:8000/api/docs。

### Docker

```bash
docker-compose up -d
```

## 功能模块

| 模块 | 功能 |
|---|---|
| **auth** | JWT 双令牌认证、登录限流、Token 黑名单 |
| **articles** | 文章 CRUD、分类/标签、Slug、阅读量统计、SEO、定时发布 |
| **comments** | 游客匿名评论、楼中楼回复、敏感词过滤、WebSocket 实时推送 |
| **guestbook** | 留言墙、游客/管理员留言 |
| **ai** | N8N 文章推送、天气查询、AI 评论回复建议 |
| **assistant** | AI 助手聊天（N8N Webhook 驱动） |
| **system** | 站点配置、敏感词管理、操作日志、定时任务、管理员站内通知 |
| **statistics** | 仪表盘统计、趋势分析、API 监控、系统健康检查 |

## 许可证

MIT License
