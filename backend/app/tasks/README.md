# Celery 异步任务

## 定时任务

| 任务 | 频率 | 说明 |
|---|---|---|
| `statistics.record_daily_snapshot` | 每天 00:05 | 记录每日统计快照 |
| `cache.clear_expired_token_blacklist` | 每小时 | 清理过期 token |
| `cache.clear_old_api_logs` | 每天 03:00 | 清理 7 天前日志 |
| `backup.database` | 每天 02:00 | pg_dump 备份，保留最近 7 个 |
| `cache.clear_expired_article_views` | 每天 01:00 | 清理 30 天前访问记录 |
| `articles.publish_due_scheduled` | 每分钟 | 发布到期定时文章 |
| `cache.clear_old_operation_logs` | 每月 1 日 4:00 | 清理旧操作日志 |

## 启动

```bash
# 开发（Worker + Beat 合一）
celery -A app.tasks.celery_app worker -B -l info -P eventlet

# 生产（分离）
celery -A app.tasks.celery_app worker -l info
celery -A app.tasks.celery_app beat -l info
```

## 邮件通知

邮件发送已从 Celery 移除，改为 asyncio 异步调用（`notification_tasks.py`），不阻塞请求。

| 场景 | 触发 |
|---|---|
| N8N 推送草稿 | `ai/router.py` |
| 系统告警 | `statistics/service.py` |

SMTP 未配置时静默跳过。
