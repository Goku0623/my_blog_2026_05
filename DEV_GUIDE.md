# 开发指南

## 修改代码后如何生效

| 修改类型 | 是否自动 | 操作 |
|---|---|---|
| 后端 `.py` | ✅ | 保存即生效（uvicorn --reload） |
| 前端 `.vue/.ts` | ✅ | 保存即生效（Vite HMR） |
| 依赖包 | ❌ | `uv sync` 或 `npm install`，重新构建 |
| 环境变量 | ❌ | 重启服务 |
| Nginx 配置 | ❌ | `nginx -s reload` |

## Docker 常用命令

```bash
docker-compose up -d                    # 启动
docker-compose restart backend          # 重启后端
docker-compose exec backend bash        # 进入容器
docker-compose logs -f backend          # 查看日志
docker-compose up -d --build backend    # 重建后端
docker-compose down                     # 停止
```
