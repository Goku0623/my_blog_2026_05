# Docker 容器化部署文档

## 目录结构

```
my_blog_2026_05/
├── backend/
│   ├── Dockerfile              # 后端多阶段构建配置
│   ├── .env.example            # 环境变量模板（完整版）
│   └── pyproject.toml          # Python 依赖管理
├── frontend/
│   └── Dockerfile              # 前端多阶段构建配置（占位）
├── nginx/
│   ├── nginx.conf              # Nginx 主配置
│   └── conf.d/
│       └── default.conf        # 站点配置（反向代理、WebSocket）
├── docker-compose.yml          # 开发环境配置
└── docker-compose.prod.yml     # 生产环境配置（覆盖）
```

## 快速开始

### 1. 开发环境

#### 初始化配置

```bash
# 复制环境变量文件
cp backend/.env.example backend/.env

# 修改必要的环境变量（数据库密码、API Key 等）
# 编辑 backend/.env
```

#### 启动所有服务

```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d
```

#### 初始化数据库

```bash
# 等待所有服务启动后，执行数据库迁移
docker-compose exec backend aerich upgrade
```

#### 访问服务

- 前端（通过 Nginx）: http://localhost
- 后端 API: http://localhost/api/
- API 文档: http://localhost/api/docs
- Flower 监控: http://localhost/flower/
- 直连后端（调试）: http://localhost:8000

#### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

#### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（清空数据库）
docker-compose down -v
```

### 2. 生产环境

#### 准备工作

```bash
# 1. 设置生产环境变量
cp backend/.env.example backend/.env

# 2. 修改生产配置
# - 设置强密码（SECRET_KEY, POSTGRES_PASSWORD, FLOWER_PASSWORD）
# - 禁用 DEBUG=false
# - 设置 APP_ENV=production
# - 配置真实的 AI API Key 和其他服务密钥

# 3. 准备 SSL 证书（如果使用 HTTPS）
mkdir -p nginx/ssl
# 将证书文件放到 nginx/ssl/ 目录
```

#### 部署启动

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose ps

# 初始化数据库
docker-compose exec backend aerich upgrade
```

#### 健康检查

```bash
# 检查服务健康状态
curl http://localhost/health

# 检查后端 API
curl http://localhost/api/health

# 查看数据库连接
docker-compose exec postgres pg_isready -U blog_user
```

## 服务架构

### 服务列表

| 服务名 | 镜像 | 端口 | 说明 |
|--------|------|------|------|
| postgres | postgres:16-alpine | 5432 | PostgreSQL 数据库 |
| redis | redis:7-alpine | 6379 | Redis 缓存和消息队列 |
| backend | backend:latest | 8000 | FastAPI 后端服务 |
| celery_worker | backend:latest | - | Celery 异步任务处理 |
| celery_beat | backend:latest | - | Celery 定时任务调度 |
| flower | backend:latest | 5555 | Celery 监控面板 |
| nginx | nginx:alpine | 80, 443 | 反向代理和静态文件服务 |

### 网络拓扑

```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │ :80, :443
                    │  (反向代理)  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  Frontend │   │  Backend  │   │   Flower  │
    │  (静态)    │   │ FastAPI   │   │  (监控)   │
    └───────────┘   └─────┬─────┘   └─────┬─────┘
                          │                │
                ┌─────────┼────────────────┘
                │         │
        ┌───────▼───┐ ┌──▼──────────┐
        │ Postgres  │ │    Redis    │
        │ (数据库)   │ │ (缓存/队列)  │
        └───────────┘ └──────┬──────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼─────┐    ┌─────▼─────┐
              │  Celery   │    │  Celery   │
              │  Worker   │    │   Beat    │
              └───────────┘    └───────────┘
```

## 环境变量说明

详见 `backend/.env.example`，核心变量：

### 必须配置

- `SECRET_KEY`: JWT 密钥（生产环境必须更改）
- `POSTGRES_PASSWORD`: 数据库密码
- `AI_API_KEY`: OpenAI API 密钥

### 推荐配置

- `CORS_ORIGINS`: 允许的跨域来源
- `RATE_LIMIT_*`: API 限流配置
- `FLOWER_USER/FLOWER_PASSWORD`: Flower 监控访问控制（生产环境）

## 数据库管理

### 数据库迁移

```bash
# 创建新迁移
docker-compose exec backend aerich migrate --name "migration_name"

# 应用迁移
docker-compose exec backend aerich upgrade

# 回滚迁移
docker-compose exec backend aerich downgrade

# 查看迁移历史
docker-compose exec backend aerich history
```

### 数据库备份

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U blog_user blog_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose exec -T postgres psql -U blog_user blog_db < backup_20260507_120000.sql
```

### 数据库连接

```bash
# 进入数据库命令行
docker-compose exec postgres psql -U blog_user -d blog_db
```

## Redis 管理

### Redis 命令行

```bash
# 进入 Redis CLI
docker-compose exec redis redis-cli

# 查看所有键
docker-compose exec redis redis-cli KEYS '*'

# 清空缓存
docker-compose exec redis redis-cli FLUSHDB
```

## Celery 任务管理

### 查看任务状态

访问 Flower 面板: http://localhost:5555

### 手动执行任务

```bash
# 进入后端容器
docker-compose exec backend python

# Python 交互式环境
>>> from app.tasks.example_task import example_task
>>> result = example_task.delay(arg1, arg2)
>>> print(result.get())
```

## 日志管理

### 查看实时日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f nginx
```

### 日志文件位置

生产环境日志挂载到宿主机：

- 应用日志: `./backend/logs/app.log`
- Nginx 日志: 容器内 `/var/log/nginx/`

## 性能优化

### 生产环境优化

1. **Backend 多进程**
   - `docker-compose.prod.yml` 已配置 `--workers 4`
   - 根据 CPU 核心数调整: `workers = (2 × CPU核心数) + 1`

2. **Redis 内存策略**
   - 已配置 `maxmemory 256mb`
   - 已配置 `maxmemory-policy allkeys-lru`

3. **Nginx 缓存**
   - 静态资源缓存 1 年
   - Gzip 压缩已启用

4. **数据库连接池**
   - `DB_POOL_MIN_SIZE=5`
   - `DB_POOL_MAX_SIZE=20`

## 安全配置

### 1. Flower 访问控制（生产环境必须）

编辑 `nginx/conf.d/default.conf`，取消注释：

```nginx
location /flower/ {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ...
}
```

生成密码文件：

```bash
# 安装 htpasswd 工具
apt-get install apache2-utils

# 生成密码
htpasswd -c nginx/.htpasswd admin

# 挂载到 nginx 容器（在 docker-compose.prod.yml 添加）
volumes:
  - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
```

### 2. HTTPS 配置

在 `nginx/conf.d/default.conf` 添加：

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... 其他配置
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

### 3. 环境变量安全

- 生产环境不要提交 `.env` 文件到 Git
- 使用强随机密码（SECRET_KEY 至少 32 字符）
- 定期轮换密钥和密码

## 故障排查

### 服务启动失败

```bash
# 查看服务状态
docker-compose ps

# 查看详细错误
docker-compose logs service_name

# 检查配置文件语法
docker-compose config
```

### 数据库连接失败

```bash
# 检查数据库健康状态
docker-compose exec postgres pg_isready

# 检查数据库日志
docker-compose logs postgres

# 验证环境变量
docker-compose exec backend env | grep POSTGRES
```

### Redis 连接失败

```bash
# 检查 Redis 服务
docker-compose exec redis redis-cli ping

# 检查 Redis 日志
docker-compose logs redis
```

### Celery 任务不执行

```bash
# 检查 worker 状态
docker-compose exec celery_worker celery -A app.tasks.celery_app inspect active

# 检查队列
docker-compose exec redis redis-cli LLEN celery

# 查看 worker 日志
docker-compose logs celery_worker
```

## 维护操作

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 应用数据库迁移
docker-compose exec backend aerich upgrade
```

### 清理 Docker 资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有未使用资源
docker system prune -a --volumes
```

### 监控容器资源

```bash
# 查看资源使用情况
docker stats

# 查看特定服务
docker stats blog_backend blog_postgres
```

## 扩展部署

### 水平扩展 Celery Worker

```bash
# 启动多个 worker 实例
docker-compose up -d --scale celery_worker=4
```

### 使用 Docker Swarm（集群部署）

```bash
# 初始化 Swarm
docker swarm init

# 部署 stack
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml blog

# 查看服务
docker service ls

# 扩展服务
docker service scale blog_celery_worker=4
```

## 最佳实践

1. **开发环境**
   - 使用 `docker-compose.yml`
   - 挂载源码实现热重载
   - 启用详细日志和调试模式

2. **生产环境**
   - 使用 `docker-compose.yml` + `docker-compose.prod.yml`
   - 不挂载源码，使用构建好的镜像
   - 配置 `restart: always`
   - 禁用 DEBUG 模式
   - 配置日志轮转
   - 定期备份数据库

3. **安全**
   - 更改所有默认密码
   - 使用 HTTPS
   - 限制 Flower 访问
   - 定期更新依赖和镜像

4. **监控**
   - 使用 Flower 监控 Celery 任务
   - 配置日志聚合（如 ELK）
   - 使用 Sentry 进行错误追踪
   - 设置健康检查和告警
