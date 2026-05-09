# 个人博客项目

基于 FastAPI + Vue3 构建的现代化个人博客系统。

## 技术栈

### 后端
- **FastAPI**: 现代化高性能 Web 框架
- **Tortoise ORM**: 异步 ORM，使用 PostgreSQL
- **Aerich**: 数据库迁移工具
- **Redis**: 缓存和会话存储
- **Celery**: 异步任务队列
- **WebSocket**: 管理端等场景的实时推送（如评论通知）

### 前端
- **Vue 3** + **TypeScript**: 组合式 API 与类型安全
- **Vite** + **Tailwind CSS 4**: 开发与样式
- **`src/ui`**: 自研轻量组件 + 工具类布局
- **Pinia / Vue Router / Axios**: 状态、路由与 HTTP

### 部署
- **Docker**: 容器化部署
- **Nginx**: 反向代理和静态文件服务

## 项目结构

```
my_blog_2026_05/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── core/              # 核心配置（数据库、安全、中间件等）
│   │   ├── modules/           # 业务模块（按功能划分）
│   │   ├── tasks/             # Celery 异步任务
│   │   └── common/            # 通用工具（异常、响应、工具函数）
│   ├── migrations/            # 数据库迁移文件
│   ├── tests/                 # 测试文件
│   └── pyproject.toml         # 依赖管理（uv）
├── frontend/                   # 前端应用（Vite + Vue3）
├── nginx/                      # Nginx 配置
├── docker-compose.yml          # 开发环境 Docker 配置
└── docker-compose.prod.yml     # 生产环境 Docker 配置
```

## 快速开始

### 环境要求

- Python 3.13+
- PostgreSQL 16+
- Redis 7+
- Node.js 20+ (前端)
- uv (Python 包管理器)

### 后端安装

1. 进入 backend 目录：
```bash
cd backend
```

2. 安装依赖（使用 uv）：
```bash
uv sync
```

3. 复制环境变量文件：
```bash
cp .env.example .env
```

4. 编辑 `.env` 文件，配置数据库和 Redis 连接信息

5. 初始化数据库迁移：
```bash
uv run aerich init-db
```

6. 创建首个管理员账号：
```bash
uv run python create_admin.py
```

这会创建默认管理员：
- 用户名: `admin`
- 密码: `admin123456`
- 邮箱: `admin@example.com`

⚠️ **重要**: 首次登录后请立即修改密码！

7. 运行开发服务器：
```bash
uv run uvicorn app.main:app --reload
```

### 前端安装（本地开发）

1. 进入 `frontend` 目录并安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器（默认通过 Vite 代理访问后端 API）：
```bash
npm run dev
```

浏览器访问：http://localhost:5173（后端需单独启动，或与 Docker 一并启动后按 compose 中的端口访问）

### 使用 Docker

开发环境：
```bash
docker-compose up -d
```

生产环境：
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 功能模块

- **auth**: 用户认证与授权（JWT）
- **articles**: 文章管理（CRUD、分类、标签）
- **comments**: 评论系统（嵌套回复）
- **ai**: AI 功能集成（天气、N8N 文章、评论回复建议等）
- **system**: 系统配置与日志
- **statistics**: 数据统计

## 开发规范

1. **包管理**: 使用 uv，依赖写入 `pyproject.toml`
2. **ORM**: 使用 tortoise-orm，迁移工具 aerich
3. **异步优先**: 所有 I/O 操作使用 async/await
4. **模块化**: 按功能模块划分，每个模块包含 models/schemas/router/service
5. **响应格式**: 统一封装为 `{"code": 0, "message": "ok", "data": ...}`
6. **异常处理**: 统一在 `app/common/exceptions.py` 处理

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 认证 API

#### 1. 登录
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123456"
}
```

响应：
```json
{
  "code": 0,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**限流**: 同一 IP 每分钟最多 10 次请求  
**登录保护**: 15 分钟内失败 5 次将被临时锁定

#### 2. 刷新令牌
```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

#### 3. 获取当前用户信息
```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

#### 4. 修改密码
```bash
PUT /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "admin123456",
  "new_password": "newSecurePassword123"
}
```

#### 5. 登出
```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

登出后，access_token 和 refresh_token 都会被加入黑名单失效。

## 已完成功能（概要）

- [x] 后端：项目结构、核心层、各业务模块（认证、文章、评论、AI、系统配置、统计等）
- [x] 认证：JWT 双令牌、登录限流与锁定、Token 黑名单、密码修改
- [x] 文章：CRUD、分类/标签、Slug、阅读量与搜索、分页与 SEO 字段
- [x] 评论：游客身份、匿名评论、嵌套回复、审核与后台管理；管理端 WebSocket 新评论通知
- [x] AI：天气查询、N8N 收文章、管理端评论 AI 回复建议（`/api/v1/ai/admin/comment-reply`）
- [x] 前端：博客前台 + 管理后台（仪表盘、文章、评论、统计、系统配置等）
- [x] 部分单元测试（`backend/tests/`，可用 `uv run pytest` 运行）

## 待办事项

- [ ] 文章/媒体资源上传（封面、正文插图等）
- [ ] Celery 定时任务与生产环境监控（Flower、告警）细化
- [ ] 扩充 E2E / 集成测试与 CI
- [ ] 生产部署与安全加固（HTTPS、密钥轮换、备份与恢复演练）

## 许可证

MIT License
