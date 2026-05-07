# Docker 快速上手指南

## 前置要求

- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose v2.0+

## 快速开始

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置（修改密码、API Key 等）
# Windows: notepad backend/.env
# Mac/Linux: nano backend/.env
```

### 2. 启动开发环境

**Windows PowerShell:**
```powershell
.\docker-manage.ps1 dev
```

**Mac/Linux:**
```bash
chmod +x docker-manage.sh
./docker-manage.sh dev

# 或使用 Makefile
make dev
```

### 3. 初始化数据库

```bash
# PowerShell
.\docker-manage.ps1 migrate

# Bash
./docker-manage.sh migrate

# Makefile
make migrate
```

### 4. 访问服务

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Flower 监控**: http://localhost:5555

## 常用命令

### PowerShell (Windows)

```powershell
# 查看所有命令
.\docker-manage.ps1 help

# 查看日志
.\docker-manage.ps1 logs backend

# 停止服务
.\docker-manage.ps1 down

# 备份数据库
.\docker-manage.ps1 backup
```

### Bash (Mac/Linux)

```bash
# 查看所有命令
./docker-manage.sh help

# 查看日志
./docker-manage.sh logs backend

# 停止服务
./docker-manage.sh down

# 备份数据库
./docker-manage.sh backup
```

### Makefile (Mac/Linux)

```bash
# 查看所有命令
make help

# 查看日志
make logs-backend

# 停止服务
make down

# 备份数据库
make backup
```

## 生产环境部署

### 1. 配置生产环境变量

```bash
# 编辑 backend/.env
APP_ENV=production
DEBUG=false
SECRET_KEY=生成一个强随机密钥（32字符以上）
POSTGRES_PASSWORD=使用强密码
FLOWER_USER=admin
FLOWER_PASSWORD=使用强密码
```

### 2. 启动生产环境

```bash
# PowerShell
.\docker-manage.ps1 prod

# Bash
./docker-manage.sh prod

# Makefile
make prod
```

### 3. 配置 HTTPS (可选)

将 SSL 证书放到 `nginx/ssl/` 目录，并修改 `nginx/conf.d/default.conf` 添加 HTTPS 配置。

详细说明请参考: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

## 常见问题

### 服务启动失败

```bash
# 查看服务状态
docker-compose ps

# 查看错误日志
docker-compose logs backend
```

### 数据库连接失败

```bash
# 检查数据库健康状态
docker-compose exec postgres pg_isready -U blog_user

# 查看数据库日志
docker-compose logs postgres
```

### 端口冲突

如果端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8080:8000"  # 将本地 8000 改为 8080
```

## 更多信息

- 完整部署文档: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- 后端 API 文档: http://localhost:8000/docs (启动后访问)
- 项目文档: [README.md](./README.md)

## 维护与支持

如遇问题，请查看：
1. [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) - 完整部署指南
2. Docker 日志: `docker-compose logs`
3. 服务状态: `docker-compose ps`
