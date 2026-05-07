# Celery 异步任务模块

使用 Celery 实现后台异步任务和定时任务，包括数据库备份、缓存清理、邮件通知、AI 处理和统计快照等功能。

## 功能特性

### ⏰ 定时任务
- **每日统计快照**: 每天 00:05 记录统计数据
- **Token 黑名单清理**: 每小时清理过期 token
- **API 日志清理**: 每天 03:00 删除 7 天前的日志
- **数据库备份**: 每天 02:00 备份并保留最近 7 个文件
- **访问记录清理**: 每天 01:00 删除 30 天前的记录

### 📨 邮件通知
- **新评论通知**: 有新评论时发送邮件给管理员
- **系统告警**: 发送系统异常或监控告警邮件

### 🗄️ 数据维护
- **数据库备份**: 使用 pg_dump 自动备份 PostgreSQL
- **日志清理**: 定期清理历史日志和访问记录
- **缓存刷新**: 手动或自动刷新敏感词缓存

### 🤖 AI 处理
- **文章后处理**: N8N 推送文章后自动生成 slug、渲染 Markdown、生成摘要

## 任务列表

### 1. backup_database
- **任务名**: `backup.database`
- **执行频率**: 每天 02:00
- **功能**: 
  - 使用 pg_dump 备份数据库
  - 文件名: `blog_backup_YYYYMMDD_HHMMSS.sql`
  - 保留最近 7 个备份文件
  - 记录操作日志

### 2. clear_expired_token_blacklist
- **任务名**: `cache.clear_expired_token_blacklist`
- **执行频率**: 每小时
- **功能**: 清理 Redis 中已过期的 token 黑名单 key

### 3. clear_old_api_logs
- **任务名**: `cache.clear_old_api_logs`
- **执行频率**: 每天 03:00
- **功能**: 删除 7 天前的 APICallLog 记录

### 4. clear_expired_article_views
- **任务名**: `cache.clear_expired_article_views`
- **执行频率**: 每天 01:00
- **功能**: 删除 30 天前的 ArticleView 记录

### 5. refresh_sensitive_words_cache
- **任务名**: `cache.refresh_sensitive_words`
- **触发方式**: 手动调用或敏感词更新后自动触发
- **功能**: 强制刷新 Redis 中的敏感词缓存

### 6. send_new_comment_notification
- **任务名**: `notification.send_new_comment_notification`
- **参数**: `comment_id: int`
- **功能**: 发送新评论邮件通知给管理员

### 7. send_alert_email
- **任务名**: `notification.send_alert_email`
- **参数**: `subject: str, message: str`
- **功能**: 发送系统告警邮件

### 8. process_n8n_article
- **任务名**: `ai.process_n8n_article`
- **参数**: `article_id: int`
- **功能**: 
  - 生成唯一 slug（基于标题）
  - 渲染 Markdown 为 HTML
  - 自动生成摘要（前 50 词）
  - 设置发布时间

### 9. record_daily_snapshot
- **任务名**: `statistics.record_daily_snapshot`
- **执行频率**: 每天 00:05
- **功能**: 记录每日统计快照（新增文章、浏览量、评论数、独立访客）

## 配置说明

### 环境变量 (.env)
```ini
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### SiteConfig 配置项
| 配置项 | 类型 | 说明 | 默认值 |
|-------|------|------|--------|
| BACKUP_DIR | str | 备份目录 | ./backups |
| ADMIN_EMAIL | str | 管理员邮箱 | - |
| SMTP_HOST | str | SMTP 服务器 | - |
| SMTP_PORT | int | SMTP 端口 | 587 |
| SMTP_USER | str | SMTP 用户名 | - |
| SMTP_PASSWORD | str | SMTP 密码 | - |
| SMTP_FROM | str | 发件人地址 | - |

## 启动命令

### 开发环境
```bash
# 同时启动 Worker 和 Beat
celery -A app.tasks.celery_app worker -B -l info -P eventlet
```

### 生产环境
```bash
# Worker（处理异步任务）
celery -A app.tasks.celery_app worker -l info

# Beat（定时任务调度器）
celery -A app.tasks.celery_app beat -l info

# Flower（监控面板）
celery -A app.tasks.celery_app flower
# 访问 http://localhost:5555
```

### Windows 系统
Windows 用户必须使用 `-P eventlet` 参数：
```bash
celery -A app.tasks.celery_app worker -B -l info -P eventlet
```

## 使用示例

### 在代码中调用任务

```python
from app.tasks.backup_tasks import backup_database
from app.tasks.cache_tasks import clear_old_api_logs
from app.tasks.notification_tasks import send_new_comment_notification

# 异步执行
backup_database.delay()
clear_old_api_logs.delay()
send_new_comment_notification.delay(comment_id=123)

# 获取结果
result = backup_database.delay()
print(result.get(timeout=10))
```

### 使用 Celery API

```python
from app.tasks.celery_app import celery_app

# 发送任务
celery_app.send_task("backup.database")
celery_app.send_task("notification.send_alert_email", 
                     args=["系统告警", "磁盘空间不足"])
```

### 定时执行任务

```python
from datetime import datetime, timedelta
from app.tasks.backup_tasks import backup_database

# 10 分钟后执行
eta = datetime.now() + timedelta(minutes=10)
backup_database.apply_async(eta=eta)
```

## 监控和调试

### 查看 Worker 状态
```bash
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect stats
```

### 查看定时任务
```bash
celery -A app.tasks.celery_app inspect scheduled
```

### 查看已注册的任务
```bash
celery -A app.tasks.celery_app inspect registered
```

### 验证配置
```bash
python -m app.tasks.test_celery
```

### 运行示例
```bash
python -m app.tasks.examples
```

## 技术实现

### 数据库连接管理
每个任务独立管理 Tortoise-ORM 连接生命周期：

```python
async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)

async def _close_db():
    await Tortoise.close_connections()

@celery_app.task(name="task.name")
def task_function():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_task_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
```

### 时区配置
```python
celery_app.conf.update(
    timezone="Asia/Shanghai",
    enable_utc=False,
)
```

### Beat Schedule
```python
beat_schedule={
    "daily-snapshot": {
        "task": "statistics.record_daily_snapshot",
        "schedule": crontab(hour=0, minute=5),
    },
    "clear-expired-blacklist": {
        "task": "cache.clear_expired_token_blacklist",
        "schedule": crontab(minute=0),
    },
    # ...
}
```

## 依赖项

### Python 包
```toml
celery[redis]>=5.4.0
redis>=5.0.4
flower>=2.0.1
markdown>=3.6
```

### 系统工具
数据库备份任务需要 PostgreSQL 客户端工具：

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql

# Windows
# 下载并安装 PostgreSQL 客户端
```

## 生产环境部署

### 使用 Supervisor

创建 `/etc/supervisor/conf.d/celery.conf`：

```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A app.tasks.celery_app worker -l info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_err.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A app.tasks.celery_app beat -l info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
```

然后重启 Supervisor：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery_worker celery_beat
```

## 故障排查

### Worker 无法启动
1. 检查 Redis 是否运行: `redis-cli ping`
2. 检查环境变量是否正确配置
3. 检查数据库连接是否正常
4. Windows 用户确保使用 `-P eventlet` 参数

### 任务执行失败
1. 查看 Worker 日志
2. 检查 SiteConfig 中的配置项（SMTP、BACKUP_DIR 等）
3. 确保 pg_dump 已安装（备份任务）
4. 验证 SMTP 配置（邮件任务）

### 定时任务不执行
1. 确保 Beat 进程正在运行
2. 检查时区设置（Asia/Shanghai）
3. 查看 Beat 日志确认任务已调度

### 邮件发送失败
1. 检查 SMTP 配置是否正确
2. 测试 SMTP 连接: `telnet smtp.gmail.com 587`
3. 确认邮箱密码（Gmail 需使用应用专用密码）
4. 检查防火墙是否阻止 SMTP 端口

## 文件说明

- `celery_app.py`: Celery 应用配置和定时任务定义
- `backup_tasks.py`: 数据库备份任务
- `cache_tasks.py`: 缓存清理任务
- `notification_tasks.py`: 邮件通知任务
- `ai_tasks.py`: AI 处理任务
- `statistics_tasks.py`: 统计快照任务
- `test_celery.py`: 配置验证脚本
- `examples.py`: 使用示例代码
