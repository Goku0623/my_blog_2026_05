# 开发指南 - 代码修改后如何生效

## 🎯 快速总结

现在配置已优化，大部分代码修改**无需重启**即可自动生效！

| 修改类型 | 是否自动生效 | 需要的操作 |
|---------|------------|-----------|
| **后端 Python 代码** | ✅ 自动 | 无需操作，保存即生效 |
| **前端 Vue/TS 代码** | ✅ 自动 | 无需操作，保存即生效 |
| **依赖包变更** | ❌ 手动 | 需要重新构建 |
| **Dockerfile 修改** | ❌ 手动 | 需要重新构建 |
| **环境变量修改** | ❌ 手动 | 需要重启服务 |
| **Nginx 配置** | ❌ 手动 | 需要重新加载配置 |

---

## 📝 详细操作指南

### 1️⃣ 日常开发（最常见）

**修改后端 Python 代码** (`.py` 文件)
```bash
# 无需任何操作！
# 保存文件后，uvicorn 的 --reload 模式会自动重启
# 刷新浏览器即可看到效果
```

**修改前端 Vue/TypeScript 代码**
```bash
# 无需任何操作！
# 保存文件后，Vite 会自动热重载（HMR）
# 浏览器会自动刷新显示最新代码
```

---

### 2️⃣ 修改依赖包

**添加/更新 Python 包** (修改 `pyproject.toml`)
```bash
# 重新构建后端相关服务
docker-compose up -d --build backend celery_worker celery_beat flower
```

**添加/更新 Node 包** (修改 `package.json`)
```bash
# 方法1：进入容器安装（推荐，更快）
docker-compose exec frontend npm install

# 方法2：重新构建（如果方法1不行）
docker-compose up -d --build frontend
```

---

### 3️⃣ 修改 Dockerfile

**修改后端 Dockerfile**
```bash
docker-compose up -d --build backend celery_worker celery_beat flower
```

**修改前端 Dockerfile**
```bash
docker-compose up -d --build frontend
```

---

### 4️⃣ 修改环境变量

**修改 `.env` 或 `.env.docker` 文件**
```bash
# 重启相关服务
docker-compose restart backend celery_worker celery_beat

# 或者完全重启所有服务
docker-compose restart
```

---

### 5️⃣ 修改 Nginx 配置

**修改 `nginx/conf.d/*.conf` 或 `nginx/nginx.conf`**
```bash
# 重新加载配置（不中断服务）
docker-compose exec nginx nginx -s reload

# 或者重启 nginx（有短暂中断）
docker-compose restart nginx
```

---

### 6️⃣ 修改 docker-compose.yml

**修改 docker-compose 配置后**
```bash
# 重新创建受影响的服务
docker-compose up -d --force-recreate <service_name>

# 例如：
docker-compose up -d --force-recreate frontend
```

---

## 🔧 常用命令速查

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# 查看最近 N 行日志
docker-compose logs --tail 50 backend
```

### 重启服务
```bash
# 重启单个服务
docker-compose restart backend
docker-compose restart frontend

# 重启所有服务
docker-compose restart

# 停止并重新启动（会重新读取配置）
docker-compose down
docker-compose up -d
```

### 重新构建
```bash
# 重新构建单个服务
docker-compose build backend
docker-compose up -d backend

# 重新构建所有服务
docker-compose build
docker-compose up -d

# 强制重新构建（不使用缓存）
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 进入容器调试
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入数据库容器
docker-compose exec postgres psql -U blog_user -d blog_db
```

---

## 🚀 完整重启流程

当遇到奇怪问题时，可以尝试完全重启：

```bash
# 1. 停止所有服务
docker-compose down

# 2. 清理（可选，会删除数据库数据）
# docker-compose down -v  # 警告：会删除所有数据！

# 3. 重新构建
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 查看日志确认启动成功
docker-compose logs -f
```

---

## 💡 开发技巧

### 1. 实时查看日志
在一个终端窗口中运行：
```bash
docker-compose logs -f backend frontend
```
这样可以同时看到前后端的实时日志。

### 2. 快速测试 API
```bash
# 直接访问后端 API（绕过 Nginx）
curl http://localhost:8000/api/health

# 查看后端 API 文档
# 浏览器打开: http://localhost:8000/docs
```

### 3. 数据库操作
```bash
# 进入数据库
docker-compose exec postgres psql -U blog_user -d blog_db

# 备份数据库
docker-compose exec postgres pg_dump -U blog_user blog_db > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U blog_user -d blog_db < backup.sql
```

---

## ⚠️ 注意事项

1. **前端热重载**：如果浏览器没有自动刷新，按 `Ctrl+F5` 强制刷新
2. **后端重载**：修改代码后，后端会自动重启，但可能需要几秒钟
3. **数据持久化**：数据库和 Redis 数据会持久化，即使重启容器也不会丢失
4. **node_modules 和 .venv**：这些目录被排除在 volume 挂载之外，避免主机和容器之间的冲突

---

## 🐛 故障排查

### 前端修改不生效
```bash
# 1. 检查前端容器是否正常运行
docker-compose logs frontend

# 2. 检查文件是否正确挂载
docker-compose exec frontend ls -la /app/src

# 3. 强制刷新浏览器（清除缓存）
# 按 Ctrl+Shift+R (Windows/Linux) 或 Cmd+Shift+R (Mac)

# 4. 重启前端容器
docker-compose restart frontend
```

### 后端修改不生效
```bash
# 1. 查看后端日志，确认是否有重载信息
docker-compose logs backend

# 2. 检查语法错误
docker-compose exec backend python -m py_compile app/main.py

# 3. 手动重启
docker-compose restart backend
```

### Nginx 502 错误
```bash
# 1. 检查后端是否运行
docker-compose ps

# 2. 检查后端健康状态
curl http://localhost:8000/api/health

# 3. 查看 nginx 错误日志
docker-compose logs nginx

# 4. 重启 nginx
docker-compose restart nginx
```

---

## 📚 相关文档

- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [FastAPI 开发文档](https://fastapi.tiangolo.com/)
- [Vite 开发文档](https://vitejs.dev/)
- [Vue 3 文档](https://vuejs.org/)

---

**祝开发愉快！ 🎉**
