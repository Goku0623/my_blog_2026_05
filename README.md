# 个人博客项目

基于 FastAPI + Vue3 构建的现代化个人博客系统。

## 技术栈

### 后端
- **FastAPI**: 现代化高性能 Web 框架
- **Tortoise ORM**: 异步 ORM，使用 PostgreSQL
- **Aerich**: 数据库迁移工具
- **Redis**: 缓存和会话存储
- **Celery**: 异步任务队列
- **WebSocket**: 实时聊天功能

### 前端
- **Vue 3**: 渐进式 JavaScript 框架
- **Vite**: 下一代前端构建工具

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
├── frontend/                   # 前端应用（待生成）
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
- **chatroom**: 实时聊天室（WebSocket）
- **ai**: AI 功能集成
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

## 已完成功能

- [x] 项目结构搭建
- [x] 数据库模型设计（所有模块）
- [x] 核心功能层（配置、数据库、安全、依赖注入、中间件）
- [x] 认证模块完整实现
  - [x] JWT 双令牌机制（access + refresh）
  - [x] 登录限流保护（每分钟10次，15分钟5次失败锁定）
  - [x] Token 黑名单机制（Redis）
  - [x] 密码修改
  - [x] 登录日志记录
- [x] 文章模块完整实现
  - [x] 文章 CRUD（草稿/发布/下架）
  - [x] 分类管理（CRUD + 删除保护）
  - [x] 标签管理（CRUD + 删除保护）
  - [x] 自动生成唯一 Slug
  - [x] 阅读量统计（Redis 24h去重）
  - [x] 全文搜索功能
  - [x] 分页列表（支持多条件过滤）
  - [x] SEO 优化字段支持

## 待办事项

- [ ] 完成前端应用初始化（Vite + Vue3）
- [ ] 实现完整的文章 CRUD API
- [ ] 实现评论系统 API
- [ ] 实现聊天室 WebSocket 功能
- [ ] 实现文件上传功能
- [ ] 配置 Celery 定时任务
- [ ] 编写单元测试
- [ ] 部署配置优化

## 许可证

MIT License
