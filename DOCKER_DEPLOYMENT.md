# Docker 部署

## 文件说明

| 文件 | 用途 |
|---|---|
| `docker-compose.yml` | 开发环境 |
| `docker-compose.prod.yml` | 生产环境（覆盖配置） |
| `nginx/conf.d/default.conf` | Nginx 反向代理 |
| `backend/Dockerfile` | 后端镜像 |
| `backend/.env.example` | 环境变量模板 |

## 快速启动

```bash
cp backend/.env.example backend/.env   # 编辑配置
docker-compose up -d
docker-compose exec backend aerich upgrade  # 初始化数据库
```

- 前端: http://localhost
- API 文档: http://localhost/api/docs

## 生产环境

```bash
cp backend/.env.example backend/.env      # 编辑生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

建议额外配置 HTTPS（参考 `nginx/conf.d/ssl.conf.example`）。
