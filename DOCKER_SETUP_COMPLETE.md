# Docker 容器化配置 - 项目总结

## 配置完成 ✅

已为项目创建完整的 Docker 容器化配置，包含开发环境和生产环境。

## 快速开始（3 步）

### 1️⃣ 配置环境变量
```powershell
# Windows PowerShell
Copy-Item backend\.env.example backend\.env

# 编辑 backend\.env，修改以下关键配置：
# - SECRET_KEY（生产环境必须更改）
# - POSTGRES_PASSWORD
# - AI_API_KEY（如果使用 AI 功能）
# - WEATHER_API_KEY（如果使用天气功能）
```

### 2️⃣ 启动服务
```powershell
# 方式 1: 使用 PowerShell 脚本（推荐）
.\docker-manage.ps1 dev

# 方式 2: 直接使用 Docker Compose
docker-compose up -d --build
```

### 3️⃣ 初始化数据库
```powershell
.\docker-manage.ps1 migrate

# 或
docker-compose exec backend aerich upgrade
```

### ✅ 访问服务
- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Flower 监控**: http://localhost:5555

## 文档导航

### 📖 核心文档

| 文档 | 用途 | 适合人群 |
|------|------|----------|
| **DOCKER_QUICKSTART.md** | 快速上手指南（5 分钟入门） | 所有人 |
| **DOCKER_DEPLOYMENT.md** | 完整部署文档（包含故障排查） | 运维、开发 |
| **DOCKER_CHECKLIST.md** | 文件清单和配置总结 | 架构师、运维 |

### 🛠️ 配置文件

| 文件 | 说明 |
|------|------|
| `backend/.env.example` | 完整环境变量模板（200+ 配置项） |
| `.env.example` | 根目录精简配置 |
| `docker-compose.yml` | 开发环境配置 |
| `docker-compose.prod.yml` | 生产环境配置 |
| `nginx/conf.d/default.conf` | Nginx 站点配置 |
| `nginx/conf.d/ssl.conf.example` | HTTPS 配置示例 |
| `redis.conf.example` | Redis 配置示例 |

### 🔧 管理工具

| 工具 | 平台 | 说明 |
|------|------|------|
| `docker-manage.ps1` | Windows | PowerShell 管理脚本 |
| `docker-manage.sh` | Linux/Mac | Bash 管理脚本 |
| `Makefile` | Linux/Mac | Make 快捷命令 |

## 常用命令速查

### Windows PowerShell

```powershell
# 查看所有命令
.\docker-manage.ps1 help

# 启动开发环境
.\docker-manage.ps1 dev

# 查看后端日志
.\docker-manage.ps1 logs backend

# 数据库迁移
.\docker-manage.ps1 migrate

# 备份数据库
.\docker-manage.ps1 backup

# 停止服务
.\docker-manage.ps1 down

# 进入后端容器
.\docker-manage.ps1 shell backend
```

### Linux/Mac (Bash)

```bash
# 赋予执行权限
chmod +x docker-manage.sh

# 启动开发环境
./docker-manage.sh dev

# 查看日志
./docker-manage.sh logs backend

# 其他命令同 PowerShell
```

### Linux/Mac (Makefile)

```bash
# 查看所有命令
make help

# 启动开发环境
make dev

# 查看后端日志
make logs-backend

# 数据库迁移
make migrate

# 备份数据库
make backup
```

## 服务架构

### 开发环境（7 个服务）

```
┌─────────────────────────────────────────────────┐
│  Nginx :80 (反向代理 + 静态文件)                 │
└────────┬────────────────────────────────────────┘
         │
    ┌────┴────┬───────────────────┐
    │         │                   │
┌───▼────┐ ┌─▼─────┐      ┌─────▼─────┐
│Frontend│ │Backend│      │  Flower   │
│ (静态) │ │ :8000 │      │  :5555    │
└────────┘ └───┬───┘      └─────┬─────┘
               │                 │
        ┌──────┴─────────────────┘
        │
    ┌───▼───┬─────────┐
    │       │         │
┌───▼──┐ ┌─▼────┐ ┌──▼─────────┐
│Postgres│Redis │ │Celery Worker│
│ :5432  │:6379 │ │+ Beat      │
└────────┘└──────┘ └────────────┘
```

### 性能配置

| 服务 | 开发环境 | 生产环境 |
|------|----------|----------|
| Backend | 1 进程 + 热重载 | 4 worker 进程 |
| Celery Worker | 4 并发 | 4 并发 |
| Redis | 256MB 内存 | 256MB 内存 + AOF |
| PostgreSQL | 默认配置 | 连接池 5-20 |

## 生产环境部署

### 额外配置步骤

1. **修改生产配置**
   ```
   backend/.env:
   - APP_ENV=production
   - DEBUG=false
   - SECRET_KEY=<生成 32+ 字符随机密钥>
   - POSTGRES_PASSWORD=<强密码>
   - FLOWER_USER=admin
   - FLOWER_PASSWORD=<强密码>
   ```

2. **（可选）配置 HTTPS**
   - 将 SSL 证书放到 `nginx/ssl/`
   - 参考 `nginx/conf.d/ssl.conf.example`

3. **启动生产环境**
   ```powershell
   .\docker-manage.ps1 prod
   ```

4. **配置 Flower 访问控制**
   ```bash
   # 生成密码文件
   htpasswd -c nginx/.htpasswd admin
   
   # 取消注释 nginx/conf.d/default.conf 中的 auth_basic 配置
   ```

## 安全检查清单

### ⚠️ 生产环境必须配置

- [ ] 更改 `SECRET_KEY`（32+ 字符）
- [ ] 更改 `POSTGRES_PASSWORD`（强密码）
- [ ] 设置 `DEBUG=false`
- [ ] 配置 `FLOWER_PASSWORD`
- [ ] 启用 HTTPS（推荐）
- [ ] 配置 CORS（`CORS_ORIGINS`）
- [ ] 启用 API 限流
- [ ] 配置防火墙规则

### 📋 推荐配置

- [ ] 配置 Flower Basic Auth
- [ ] 设置定期数据库备份
- [ ] 配置日志轮转
- [ ] 启用 Sentry 错误追踪
- [ ] 配置 SSL/TLS
- [ ] 设置监控告警

## 数据持久化

### 数据卷位置

| 数据 | Docker Volume | 说明 |
|------|---------------|------|
| PostgreSQL | `postgres_data` | 数据库文件 |
| Redis | `redis_data` | RDB/AOF 文件 |
| 上传文件 | `./backend/uploads` (生产) | 用户上传 |
| 日志 | `./backend/logs` (生产) | 应用日志 |

### 备份和恢复

```powershell
# 备份数据库
.\docker-manage.ps1 backup

# 恢复数据库
.\docker-manage.ps1 restore backups\backup_20260507_120000.sql
```

## 故障排查

### 服务启动失败

```powershell
# 查看服务状态
docker-compose ps

# 查看错误日志
docker-compose logs backend
```

### 数据库连接失败

```powershell
# 检查数据库健康
docker-compose exec postgres pg_isready -U blog_user

# 查看数据库日志
docker-compose logs postgres
```

### 端口冲突

修改 `docker-compose.yml` 端口映射：
```yaml
ports:
  - "8080:8000"  # 改为其他可用端口
```

## CI/CD 自动化（可选）

参考 `.github-workflows-example.yml` 配置 GitHub Actions：
- 自动化测试
- Docker 镜像构建
- 自动部署到生产服务器

## 性能优化建议

### 生产环境

1. **Backend Workers**: 根据 CPU 调整（推荐 `(2 × CPU核心数) + 1`）
2. **Celery Concurrency**: 根据任务类型调整
3. **Database Pool**: 根据连接数需求调整 `DB_POOL_MAX_SIZE`
4. **Redis Memory**: 根据缓存需求调整 `maxmemory`

### Nginx

- 启用 HTTP/2
- 配置 CDN
- 优化静态资源缓存
- 启用 Brotli 压缩（可选）

## 下一步行动

### 立即执行

1. [ ] 复制 `backend/.env.example` 到 `backend/.env`
2. [ ] 填写必要的环境变量（数据库密码、API Key）
3. [ ] 运行 `.\docker-manage.ps1 dev` 启动开发环境
4. [ ] 执行数据库迁移 `.\docker-manage.ps1 migrate`
5. [ ] 访问 http://localhost 验证服务

### 后续任务

1. [ ] 阅读 `DOCKER_DEPLOYMENT.md` 了解详细配置
2. [ ] 根据需求调整配置参数
3. [ ] 配置生产环境（如果需要）
4. [ ] 设置定期备份任务
5. [ ] 配置监控和告警

## 技术栈

- **容器化**: Docker + Docker Compose
- **后端**: Python 3.13 + FastAPI + Uvicorn
- **数据库**: PostgreSQL 16
- **缓存/队列**: Redis 7
- **异步任务**: Celery + Flower
- **Web 服务器**: Nginx
- **包管理**: uv (Python)
- **ORM**: Tortoise ORM + Aerich

## 支持和文档

| 资源 | 链接/说明 |
|------|----------|
| 快速开始 | `DOCKER_QUICKSTART.md` |
| 完整文档 | `DOCKER_DEPLOYMENT.md` |
| 文件清单 | `DOCKER_CHECKLIST.md` |
| API 文档 | http://localhost:8000/docs（启动后） |
| 环境变量 | `backend/.env.example` |

## 常见问题

**Q: 如何在 Windows 运行 bash 脚本？**  
A: 使用 PowerShell 脚本 `docker-manage.ps1`，功能完全相同。

**Q: 端口被占用怎么办？**  
A: 修改 `docker-compose.yml` 中的端口映射。

**Q: 如何扩展 Worker 数量？**  
A: `docker-compose up -d --scale celery_worker=4`

**Q: 数据保存在哪里？**  
A: Docker 数据卷，运行 `docker volume ls` 查看。

**Q: 如何完全重置？**  
A: `.\docker-manage.ps1 down:volumes` 删除所有数据。

## 项目状态

✅ Docker 配置完成  
✅ 开发环境配置完成  
✅ 生产环境配置完成  
✅ 管理脚本完成  
✅ 文档完成  
✅ 安全配置完成  

🎉 **现在可以开始使用 Docker 进行开发了！**

---

**需要帮助？**
1. 查看 `DOCKER_QUICKSTART.md` 快速开始
2. 查看 `DOCKER_DEPLOYMENT.md` 详细文档
3. 运行 `.\docker-manage.ps1 help` 查看所有命令
