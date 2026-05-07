# Docker 容器化配置文件清单

## 已创建的文件

### 核心 Docker 配置

#### 1. **backend/Dockerfile**
多阶段构建配置，包含三个阶段：
- **base**: 基础镜像，安装 uv 和系统依赖（postgresql-client）
- **development**: 开发环境，支持热重载
- **production**: 生产环境，多进程运行（4 workers）

特点：
- 使用 Python 3.13-slim 作为基础镜像
- 非 root 用户运行（appuser, uid=1000）
- 使用 uv 进行快速依赖安装

#### 2. **frontend/Dockerfile**
前端多阶段构建模板（占位），包含三个阶段：
- **builder**: 构建阶段，编译前端资源
- **development**: 开发环境，Vite 开发服务器
- **production**: 生产环境，Nginx 提供静态文件服务

#### 3. **docker-compose.yml**
开发环境完整配置，包含以下服务：
- **postgres**: PostgreSQL 16 数据库，带健康检查
- **redis**: Redis 7 缓存和消息队列，配置内存限制和 LRU 策略
- **backend**: FastAPI 后端服务，热重载模式
- **celery_worker**: Celery 异步任务处理（4 并发）
- **celery_beat**: Celery 定时任务调度
- **flower**: Celery 监控面板
- **nginx**: 反向代理和静态文件服务

特点：
- 使用健康检查确保服务依赖正确启动
- 挂载源码实现开发热重载
- 环境变量从 `backend/.env` 读取
- 自动创建数据卷持久化数据

#### 4. **docker-compose.prod.yml**
生产环境配置覆盖文件，主要改动：
- 使用 `production` 构建目标
- 移除源码挂载（使用镜像内代码）
- 后端使用 4 个 worker 进程
- 所有服务添加 `restart: always`
- Celery Worker 日志级别调整为 warning
- Flower 配置 Basic Auth 认证
- 挂载日志和上传目录到宿主机
- 挂载 SSL 证书目录

使用方式：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Nginx 配置

#### 5. **nginx/nginx.conf**
Nginx 主配置文件（已存在，未修改）：
- 工作进程自动分配
- 启用 Gzip 压缩
- 日志格式配置
- 包含 conf.d 目录下的所有配置

#### 6. **nginx/conf.d/default.conf**
站点配置文件，包含：
- **前端路由**: 静态文件服务，支持 SPA 路由
- **后端 API**: 反向代理到 backend:8000
- **WebSocket**: 支持 /ws/ 路径的 WebSocket 连接
- **Flower 监控**: 反向代理到 flower:5555，可配置 Basic Auth
- **健康检查**: /health 端点
- **静态资源缓存**: JS/CSS/图片等缓存 1 年
- **文件上传限制**: 10MB

#### 7. **nginx/conf.d/ssl.conf.example**
HTTPS 配置示例，包含：
- HTTP 到 HTTPS 自动重定向
- SSL/TLS 安全配置（TLS 1.2+）
- HSTS 安全头
- Let's Encrypt ACME 验证支持
- 完整的安全响应头配置

### 环境变量配置

#### 8. **backend/.env.example**
完整的后端环境变量模板，包含：
- **应用配置**: APP_ENV, DEBUG, SECRET_KEY
- **JWT 配置**: 算法、过期时间
- **服务器配置**: HOST, PORT, CORS
- **数据库配置**: PostgreSQL 连接参数和连接池
- **Redis 配置**: 连接参数和缓存 TTL
- **Celery 配置**: Broker、Backend、时区、超时
- **Flower 配置**: 用户名、密码（生产环境）
- **AI 服务**: N8N Webhook、OpenAI API 配置
- **天气服务**: 提供商、API Key
- **文件上传**: 目录、大小限制、允许扩展名
- **限流配置**: 全局限流和 API 特定限流
- **日志配置**: 级别、文件、轮转
- **邮件配置**: SMTP 服务器配置
- **备份配置**: 目录、保留天数
- **安全配置**: 密码哈希、会话、CSRF
- **功能开关**: Feature flags
- **监控配置**: Sentry、Google Analytics
- **开发工具**: 热重载、SQL 日志

#### 9. **.env.example**
根目录环境变量模板（精简版），主要用于 docker-compose.yml：
- 应用环境和调试模式
- 服务端口配置
- 数据库连接参数
- Redis 连接参数
- Flower 认证信息
- 引导用户查看完整配置 `backend/.env.example`

### Docker 优化文件

#### 10. **backend/.dockerignore**
后端 Docker 构建忽略文件：
- Python 缓存和编译文件
- 虚拟环境
- 环境变量文件
- IDE 配置
- 测试和日志文件
- 数据库文件和迁移
- 上传文件和备份
- Docker 和 Git 文件
- 文档文件

#### 11. **frontend/.dockerignore**
前端 Docker 构建忽略文件：
- node_modules
- 构建输出
- 环境变量文件
- IDE 配置
- 测试覆盖率
- 日志文件
- Docker 和 Git 文件
- 文档文件

### 管理脚本

#### 12. **docker-manage.sh** (Linux/Mac)
Bash 脚本，提供便捷的 Docker 管理命令：
- `dev`: 启动开发环境
- `prod`: 启动生产环境
- `down`: 停止服务
- `down:volumes`: 停止并删除数据卷
- `restart`: 重启服务
- `logs [service]`: 查看日志
- `status`: 查看服务状态
- `migrate`: 执行数据库迁移
- `migrate:create <name>`: 创建新迁移
- `backup`: 备份数据库
- `restore <file>`: 恢复数据库
- `shell [service]`: 进入容器 shell
- `stats`: 查看资源使用
- `clean`: 清理 Docker 资源
- `clean:all`: 深度清理

#### 13. **docker-manage.ps1** (Windows)
PowerShell 脚本，功能与 bash 版本相同：
- 颜色输出支持
- Windows 路径兼容
- 交互式确认
- 所有与 bash 版本相同的命令

#### 14. **Makefile** (Linux/Mac)
Make 命令快捷方式：
- `make dev`: 启动开发环境
- `make prod`: 启动生产环境
- `make down`: 停止服务
- `make logs-backend`: 查看后端日志
- `make logs-celery`: 查看 Celery 日志
- `make migrate`: 数据库迁移
- `make backup`: 备份数据库
- `make shell`: 进入后端容器
- `make shell-db`: 进入数据库
- `make shell-redis`: 进入 Redis
- `make clean`: 清理资源

### 配置示例文件

#### 15. **redis.conf.example**
Redis 配置文件示例：
- 内存限制和淘汰策略
- RDB 快照持久化配置
- AOF 持久化配置
- 慢查询日志
- 客户端连接数限制
- TCP keepalive 配置

### 文档

#### 16. **DOCKER_DEPLOYMENT.md**
完整的 Docker 部署文档，包含：
- 目录结构说明
- 快速开始指南（开发 & 生产）
- 服务架构和网络拓扑图
- 环境变量详细说明
- 数据库管理（迁移、备份、恢复）
- Redis 管理
- Celery 任务管理
- 日志管理
- 性能优化建议
- 安全配置（Flower Auth、HTTPS、密钥管理）
- 故障排查指南
- 维护操作（更新代码、清理资源、监控）
- 扩展部署（水平扩展、Docker Swarm）
- 最佳实践总结

#### 17. **DOCKER_QUICKSTART.md**
快速上手指南（精简版）：
- 前置要求
- 三步快速启动
- 常用命令速查（PowerShell、Bash、Makefile）
- 生产环境部署步骤
- 常见问题快速解决
- 相关文档链接

#### 18. **DOCKER_CHECKLIST.md** (本文件)
文件清单和配置总结

### CI/CD 示例

#### 19. **.github-workflows-example.yml**
GitHub Actions CI/CD 配置示例：
- 自动化测试（使用 PostgreSQL 和 Redis 服务）
- Docker 镜像构建和推送（GitHub Container Registry）
- 自动部署到生产服务器
- 分支策略（develop、main）
- 秘钥配置说明

### 其他文件

#### 20. **.gitignore**
更新了 Docker 相关的忽略规则：
- 移除了对 `.dockerignore` 的忽略（重要配置文件）
- 保留备份文件忽略
- 保留日志和上传目录忽略

## 文件结构总览

```
my_blog_2026_05/
├── backend/
│   ├── Dockerfile                # 后端多阶段构建
│   ├── .dockerignore             # 构建忽略文件
│   ├── .env.example              # 完整环境变量模板
│   └── pyproject.toml            # Python 依赖管理
│
├── frontend/
│   ├── Dockerfile                # 前端多阶段构建（模板）
│   └── .dockerignore             # 构建忽略文件
│
├── nginx/
│   ├── nginx.conf                # Nginx 主配置
│   └── conf.d/
│       ├── default.conf          # 站点配置（HTTP）
│       └── ssl.conf.example      # HTTPS 配置示例
│
├── docker-compose.yml            # 开发环境配置
├── docker-compose.prod.yml       # 生产环境配置
├── .env.example                  # 根目录环境变量模板
├── redis.conf.example            # Redis 配置示例
│
├── docker-manage.sh              # Linux/Mac 管理脚本
├── docker-manage.ps1             # Windows 管理脚本
├── Makefile                      # Make 快捷命令
│
├── DOCKER_DEPLOYMENT.md          # 完整部署文档
├── DOCKER_QUICKSTART.md          # 快速上手指南
├── DOCKER_CHECKLIST.md           # 本文件（文件清单）
│
├── .github-workflows-example.yml # CI/CD 配置示例
└── .gitignore                    # Git 忽略规则（已更新）
```

## 使用流程

### 首次部署

1. **配置环境变量**
   ```bash
   cp backend/.env.example backend/.env
   # 编辑 backend/.env，填写必要配置
   ```

2. **启动开发环境**
   ```bash
   # Windows
   .\docker-manage.ps1 dev
   
   # Linux/Mac (Bash)
   ./docker-manage.sh dev
   
   # Linux/Mac (Make)
   make dev
   ```

3. **初始化数据库**
   ```bash
   # Windows
   .\docker-manage.ps1 migrate
   
   # Linux/Mac
   ./docker-manage.sh migrate
   # 或
   make migrate
   ```

4. **访问服务**
   - 前端: http://localhost
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/docs
   - Flower: http://localhost:5555

### 生产部署

1. **配置生产环境变量**
   ```bash
   # 编辑 backend/.env
   APP_ENV=production
   DEBUG=false
   SECRET_KEY=<生成强随机密钥>
   POSTGRES_PASSWORD=<强密码>
   FLOWER_USER=admin
   FLOWER_PASSWORD=<强密码>
   ```

2. **（可选）配置 HTTPS**
   - 将 SSL 证书放到 `nginx/ssl/`
   - 参考 `nginx/conf.d/ssl.conf.example`
   - 修改 `docker-compose.prod.yml` 挂载证书

3. **启动生产环境**
   ```bash
   # Windows
   .\docker-manage.ps1 prod
   
   # Linux/Mac
   ./docker-manage.sh prod
   # 或
   make prod
   ```

4. **配置 Flower Basic Auth**
   ```bash
   # 生成密码文件
   htpasswd -c nginx/.htpasswd admin
   
   # 取消注释 nginx/conf.d/default.conf 中的 auth_basic 配置
   ```

### 日常维护

- **查看日志**: `docker-manage.ps1 logs [service]`
- **备份数据库**: `docker-manage.ps1 backup`
- **更新代码**: `git pull && docker-manage.ps1 prod`
- **清理资源**: `docker-manage.ps1 clean`

## 配置检查清单

### 开发环境

- [ ] 复制 `backend/.env.example` 到 `backend/.env`
- [ ] 填写基本配置（数据库密码可使用默认值）
- [ ] 运行 `docker-manage.ps1 dev` 或 `make dev`
- [ ] 执行数据库迁移
- [ ] 访问 http://localhost 验证服务

### 生产环境

- [ ] 配置强密码（SECRET_KEY, POSTGRES_PASSWORD, FLOWER_PASSWORD）
- [ ] 设置 `APP_ENV=production` 和 `DEBUG=false`
- [ ] 配置 AI API Key 和其他服务密钥
- [ ] （可选）配置 SSL 证书
- [ ] （推荐）配置 Flower Basic Auth
- [ ] 配置防火墙规则
- [ ] 设置定期备份任务
- [ ] 配置日志轮转
- [ ] 运行 `docker-manage.ps1 prod` 或 `make prod`
- [ ] 执行数据库迁移
- [ ] 验证所有服务正常运行

### 安全检查

- [ ] 所有密码和密钥已更改（不使用默认值）
- [ ] 数据库端口未暴露到公网（或配置防火墙）
- [ ] Flower 配置了访问控制（Basic Auth）
- [ ] 启用 HTTPS（生产环境）
- [ ] CORS 配置正确
- [ ] 文件上传大小限制合理
- [ ] API 限流已配置
- [ ] `.env` 文件未提交到 Git

### 监控和备份

- [ ] 配置 Sentry 错误追踪（可选）
- [ ] 设置定期数据库备份
- [ ] 配置日志收集和分析
- [ ] 监控磁盘空间使用
- [ ] 监控 Docker 容器状态
- [ ] 设置告警通知

## 常见问题

### Q: 如何在 Windows 上运行 bash 脚本？

A: 使用 PowerShell 脚本 `docker-manage.ps1` 或安装 Git Bash、WSL。

### Q: 端口被占用怎么办？

A: 修改 `docker-compose.yml` 中的端口映射，例如 `"8080:8000"`。

### Q: 如何扩展 Celery Worker？

A: 运行 `docker-compose up -d --scale celery_worker=4`。

### Q: 如何查看容器内的文件？

A: 运行 `docker-manage.ps1 shell backend` 进入容器。

### Q: 数据库数据保存在哪里？

A: Docker 数据卷 `postgres_data`，可通过 `docker volume inspect blog_postgres_data` 查看。

### Q: 如何完全重置环境？

A: 运行 `docker-manage.ps1 down:volumes` 删除所有数据，然后重新启动。

## 性能优化建议

1. **生产环境优化**
   - 根据 CPU 核心数调整 Backend workers: `(2 × CPU核心数) + 1`
   - 调整 Celery Worker 并发数: `-c <worker数量>`
   - 优化 PostgreSQL 连接池大小

2. **Redis 优化**
   - 根据实际需求调整 `maxmemory`
   - 选择合适的淘汰策略
   - 启用 AOF 持久化（生产环境）

3. **Nginx 优化**
   - 启用 HTTP/2
   - 配置静态资源缓存
   - 开启 Gzip 压缩
   - 使用 CDN 分发静态资源

4. **Docker 优化**
   - 使用多阶段构建减小镜像大小
   - 合理配置 `.dockerignore`
   - 使用构建缓存加速构建

## 下一步

- 根据实际需求调整配置
- 阅读完整文档 `DOCKER_DEPLOYMENT.md`
- 配置 CI/CD 自动化部署（参考 `.github-workflows-example.yml`）
- 设置监控和告警系统
- 配置定期备份任务
- 进行性能测试和优化

## 技术栈总结

- **容器化**: Docker + Docker Compose
- **后端**: Python 3.13 + FastAPI + uvicorn
- **数据库**: PostgreSQL 16
- **缓存/队列**: Redis 7
- **异步任务**: Celery + Flower
- **Web 服务器**: Nginx
- **包管理**: uv (Python), npm/yarn (Node.js)
- **ORM**: Tortoise ORM + Aerich
- **部署**: 多阶段构建 + 开发/生产环境分离

## 联系支持

如遇到问题：
1. 查看 `DOCKER_DEPLOYMENT.md` 故障排查部分
2. 运行 `docker-compose logs` 查看错误日志
3. 检查 `backend/.env` 配置是否正确
4. 确认 Docker 和 Docker Compose 版本
