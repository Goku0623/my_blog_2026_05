# 统计模块

## 功能

- **仪表盘**: 总文章/已发布/草稿/总阅读/今日数据（Redis 缓存 60 秒）
- **趋势分析**: 阅读/评论/文章/访客，日/周/月维度
- **API 监控**: 调用量/响应时间/错误率/Top Endpoint
- **系统健康检查**: PostgreSQL/Redis/Celery/Disk，健康/降级/故障三级状态
- **告警通知**: 系统异常时自动通知管理员（站内通知 + 邮件）

## API 端点

| 端点 | 说明 |
|---|---|
| `/admin/statistics/dashboard` | 仪表盘数据 |
| `/admin/statistics/trends` | 趋势数据 |
| `/admin/statistics/api-monitor` | API 监控 |
| `/admin/statistics/health` | 系统健康检查 |
| `/admin/statistics/articles/top-viewed` | 热门文章 |
| `/admin/statistics/comments/recent` | 最近评论活动 |
