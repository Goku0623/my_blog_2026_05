# Docker 部署

## 文件说明

| 文件 | 用途 |
|---|---|
| `docker-compose.yml` | 开发环境 |
| `docker-compose.prod.yml` | 生产环境（覆盖配置） |
| `nginx/conf.d/default.conf` | Nginx 反向代理 |
| `backend/Dockerfile` | 后端镜像 |
| `.env.example` | Docker 编排环境变量模板（数据库端口、Flower 账号等） |
| `backend/.env.docker.example` | 应用容器环境变量模板 |

## 快速启动

```bash
cp .env.example .env                              # 编辑 Docker 编排配置
cp backend/.env.docker.example backend/.env.docker  # 编辑应用配置
docker-compose up -d
docker-compose exec backend aerich upgrade  # 初始化数据库
```

- 前端: http://localhost
- API 文档: http://localhost/api/docs

## 生产环境

```bash
cp .env.example .env                              # 编辑 Docker 编排配置
cp backend/.env.docker.example backend/.env.docker  # 编辑生产应用配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

建议额外配置 HTTPS（参考 `nginx/conf.d/ssl.conf.example`）。

## 上线前最终检查清单

```bash
# 1) 准备配置文件（首次）
cp .env.example .env
cp backend/.env.docker.example backend/.env.docker

# 2) 修改配置（至少检查以下项）
# - .env: POSTGRES_PASSWORD, FLOWER_USER, FLOWER_PASSWORD
# - backend/.env.docker: SECRET_KEY, DEBUG=false, DATABASE_URL, REDIS_URL, SMTP/AI 等生产参数

# 3) 校验 Compose 生产合并配置
docker compose -f docker-compose.yml -f docker-compose.prod.yml config -q

# 4) 启动生产容器
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 5) 执行数据库迁移
docker compose exec backend aerich upgrade

# 6) 基础健康检查
# - http://<your-domain>/health
# - http://<your-domain>/api/docs
```

## 清理测试数据（保留管理员与系统配置）

当你确认当前数据都是测试数据时，可使用以下命令清理：

```bash
# 仅清理业务测试数据（推荐）
docker compose exec backend python -m scripts.purge_test_data --yes

# 若连上传资源也要清空（会删除 backend/uploads 内容）
docker compose exec backend python -m scripts.purge_test_data --yes --clear-uploads
```

脚本默认保留：
- `admin_users`
- `site_configs`
- `scheduled_tasks`
- `sensitive_words`
