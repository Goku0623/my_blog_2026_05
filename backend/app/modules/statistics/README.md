# 统计与监控模块（Statistics）

## 功能概述

统计与监控模块提供完整的系统数据统计、API监控、性能追踪和服务健康检查功能，支持仪表盘展示、趋势分析、实时监控和告警通知。

## 核心功能

### 1. 仪表盘统计

- **实时数据展示**：总文章数、已发布、草稿、总阅读量
- **今日数据**：今日阅读、评论、新增文章
- **Redis 缓存**：60 秒缓存优化，降低数据库压力

### 2. 趋势分析

- **多维度指标**：阅读量（views）、评论（comments）、文章（articles）、访客（visitors）
- **多时间周期**：日（30天）、周（12周）、月（12个月）
- **数据预聚合**：优先读取 DailyStats 表，无数据时实时聚合
- **可视化支持**：返回标准化数据格式，便于前端图表渲染

### 3. API 监控

- **调用统计**：总调用量、平均响应时间、错误率
- **热门接口**：Top 10 接口按调用量排序
- **性能指标**：每个接口的响应时间、成功率、错误数
- **错误追踪**：最近 10 条错误日志，含详细信息
- **时间范围**：支持查询最近 1-168 小时的数据

### 4. Celery 任务统计

- **任务监控**：各任务的执行次数、成功、失败、待处理
- **性能分析**：平均运行时间统计
- **状态检查**：通过 Celery inspect 获取实时状态

### 5. 系统健康检查

- **服务检测**：PostgreSQL、Redis、Celery Worker、磁盘空间
- **并发检查**：异步并发检测，超时 3 秒
- **三级状态**：
  - `healthy`：服务正常
  - `degraded`：服务降级（如磁盘使用超 80%）
  - `unhealthy`：服务故障
- **延迟监控**：记录每个服务的响应延迟

### 6. 扩展统计

- **热门文章**：按阅读量排序的 Top N 文章
- **评论活动**：按最新评论时间排序的文章活跃度

## API 端点

### 管理员端点（需要认证）

#### 获取仪表盘数据
```http
GET /api/v1/admin/statistics/dashboard
Authorization: Bearer {access_token}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_articles": 125,
    "published_articles": 98,
    "draft_articles": 27,
    "total_views": 15234,
    "total_comments": 432,
    "pending_comments": 12,
    "today_views": 234,
    "today_comments": 18,
    "today_new_articles": 2
  }
}
```

#### 获取趋势数据
```http
GET /api/v1/admin/statistics/trends?metric=views&period=day
Authorization: Bearer {access_token}
```

**查询参数：**
- `metric`：指标类型（views | comments | articles | visitors）
- `period`：时间周期（day | week | month）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "period": "day",
    "metric": "views",
    "data": [
      {"date": "2026-04-08", "value": 450},
      {"date": "2026-04-09", "value": 523},
      {"date": "2026-04-10", "value": 498}
    ]
  }
}
```

#### API 监控数据
```http
GET /api/v1/admin/statistics/api-monitor?hours=24
Authorization: Bearer {access_token}
```

**查询参数：**
- `hours`：查询时间范围（1-168 小时，默认 24）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_calls": 8523,
    "avg_response_ms": 45.23,
    "error_rate": 0.02,
    "top_endpoints": [
      {
        "endpoint": "/api/v1/articles",
        "method": "GET",
        "call_count": 2341,
        "avg_response_ms": 32.5,
        "success_rate": 0.99,
        "error_count": 23
      }
    ],
    "recent_errors": [
      {
        "endpoint": "/api/v1/articles/999",
        "method": "GET",
        "status_code": 404,
        "error_message": "Article not found",
        "ip_address": "192.168.1.100",
        "created_at": "2026-05-07T10:30:45"
      }
    ]
  }
}
```

#### Celery 任务统计
```http
GET /api/v1/admin/statistics/celery
Authorization: Bearer {access_token}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "task_name": "app.tasks.send_email",
      "total": 1523,
      "succeeded": 1498,
      "failed": 25,
      "pending": 3,
      "avg_runtime_ms": 234.5
    }
  ]
}
```

#### 系统健康检查
```http
GET /api/v1/admin/statistics/health
Authorization: Bearer {access_token}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "overall_status": "healthy",
    "services": [
      {
        "service": "PostgreSQL",
        "status": "healthy",
        "latency_ms": 12.34,
        "detail": null
      },
      {
        "service": "Redis",
        "status": "healthy",
        "latency_ms": 2.45,
        "detail": null
      },
      {
        "service": "Celery Worker",
        "status": "healthy",
        "latency_ms": 45.67,
        "detail": "2 workers active"
      },
      {
        "service": "Disk Space",
        "status": "healthy",
        "latency_ms": 0.23,
        "detail": "450.23GB free of 500.00GB (10.0% used)"
      }
    ],
    "checked_at": "2026-05-07T10:45:23"
  }
}
```

#### 热门文章统计
```http
GET /api/v1/admin/statistics/articles/top-viewed?limit=10
Authorization: Bearer {access_token}
```

**查询参数：**
- `limit`：返回数量（1-50，默认 10）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": 123,
      "title": "Python 异步编程完全指南",
      "slug": "python-async-programming-guide",
      "view_count": 5234,
      "published_at": "2026-04-15T08:30:00"
    }
  ]
}
```

#### 最近评论活动
```http
GET /api/v1/admin/statistics/comments/recent?limit=10
Authorization: Bearer {access_token}
```

**查询参数：**
- `limit`：返回数量（1-50，默认 10）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "article_id": 123,
      "article_title": "Python 异步编程完全指南",
      "comment_count": 45,
      "latest_comment_at": "2026-05-07T09:15:32"
    }
  ]
}
```

## 数据模型

### DailyStats（每日统计快照）
```python
- id: 主键
- stat_date: 统计日期（唯一）
- new_articles: 当日新增文章
- total_views: 累计阅读量
- new_comments: 当日新增评论
- unique_visitors: 当日独立访客
- created_at: 创建时间
```

### APICallLog（API 调用日志）
```python
- id: 主键
- endpoint: 接口路径
- method: HTTP 方法
- status_code: 响应状态码
- response_time_ms: 响应时间（毫秒）
- ip_address: 客户端 IP
- error_message: 错误信息（可选）
- created_at: 创建时间
```

## 使用示例

### 1. 快速开始

#### 数据库迁移
```bash
# 使用 aerich 创建迁移
cd backend
aerich migrate --name add_statistics_tables
aerich upgrade
```

**手动创建表（如果 aerich 不可用）：**
```sql
-- 创建 daily_stats 表
CREATE TABLE IF NOT EXISTS daily_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE UNIQUE NOT NULL,
    new_articles INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    new_comments INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_daily_stats_stat_date ON daily_stats(stat_date);

-- 创建 api_call_logs 表
CREATE TABLE IF NOT EXISTS api_call_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_call_logs_created_at ON api_call_logs(created_at);
CREATE INDEX idx_api_call_logs_endpoint ON api_call_logs(endpoint);
```

### 2. 编程接口

#### 获取统计数据
```python
from app.modules.statistics.service import StatisticsService

# 获取仪表盘数据
dashboard_data = await StatisticsService.get_dashboard_data()
print(f"总文章数: {dashboard_data.total_articles}")

# 获取趋势数据
trend_data = await StatisticsService.get_trend_data(
    metric="views",
    period="day"
)
print(f"趋势数据点数: {len(trend_data.data)}")

# 系统健康检查
health = await StatisticsService.check_system_health()
print(f"系统状态: {health.overall_status}")
for service in health.services:
    print(f"- {service.service}: {service.status}")
```

#### 记录每日快照
```python
from app.modules.statistics.service import StatisticsService

# 手动记录快照（通常由 Celery 定时任务调用）
await StatisticsService.record_daily_snapshot()

# 发送告警通知
await StatisticsService.send_alert_notification(
    subject="系统磁盘空间不足",
    message="磁盘使用率已超过 85%，请及时清理"
)
```

### 3. Celery 定时任务配置（可选）

在 Celery 应用配置中添加定时任务：

```python
# app/tasks/celery_app.py 或相关配置文件
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 每日 0:00 记录数据快照
    'record-daily-stats': {
        'task': 'app.modules.statistics.tasks.record_daily_snapshot',
        'schedule': crontab(hour=0, minute=0),
    },
    # 每周日 2:00 清理历史日志（保留最近 30 天）
    'cleanup-old-api-logs': {
        'task': 'app.modules.statistics.tasks.cleanup_old_api_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
        'args': (30,),
    },
}
```

启动 Celery Beat：
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### 4. 数据维护

#### 清理历史日志
```python
import asyncio
from app.modules.statistics.tasks import cleanup_old_api_logs

# 清理 30 天前的日志
asyncio.run(cleanup_old_api_logs(days=30))
```

#### SQL 查询示例
```sql
-- 查询最近 7 天的统计数据
SELECT * FROM daily_stats 
WHERE stat_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY stat_date DESC;

-- 查询错误率最高的接口
SELECT 
    endpoint,
    method,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    ROUND(100.0 * SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
FROM api_call_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint, method
HAVING COUNT(*) > 10
ORDER BY error_rate DESC
LIMIT 10;
```

## 配置说明

### 环境变量

所有必需的环境变量已在 `.env` 中配置：
```env
DATABASE_URL=postgres://blog_user:password@localhost:5432/blog_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 中间件配置

API 日志中间件已在 `app/core/middleware.py` 中自动配置，会自动记录所有 API 请求到 `api_call_logs` 表。

### 缓存配置

- **仪表盘数据**：Redis 缓存 60 秒

## 性能优化

### 1. 数据库索引

确保已创建以下索引：
```sql
CREATE INDEX IF NOT EXISTS idx_api_call_logs_created_at ON api_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_call_logs_endpoint ON api_call_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_daily_stats_stat_date ON daily_stats(stat_date);
```

### 2. 缓存策略

- 仪表盘数据使用 Redis 缓存 60 秒
- 趋势数据依赖 DailyStats 预聚合，查询效率高
- API 监控实时聚合，建议按小时缓存结果

### 3. 数据清理

定期清理历史日志，避免数据量过大：
```python
# 通过 Celery 定时任务自动清理
# 或手动执行 SQL
DELETE FROM api_call_logs WHERE created_at < NOW() - INTERVAL '30 days';
```

### 4. 分区表（大数据量场景）

如果 API 日志数据量很大，可考虑按时间分区：
```sql
-- PostgreSQL 10+ 分区表示例
CREATE TABLE api_call_logs_partitioned (
    LIKE api_call_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE api_call_logs_2026_05 
PARTITION OF api_call_logs_partitioned
FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

## 监控告警

### 配置告警规则

创建 Celery 定时任务检查系统状态并发送告警：

```python
from celery import shared_task
from app.modules.statistics.service import StatisticsService

@shared_task
async def check_system_alerts():
    # 检查系统健康
    health = await StatisticsService.check_system_health()
    if health.overall_status == "unhealthy":
        await StatisticsService.send_alert_notification(
            subject="系统健康检查失败",
            message=f"检测到系统服务故障"
        )
    
    # 检查 API 错误率
    api_metrics = await StatisticsService.get_api_metrics(hours=1)
    if api_metrics.error_rate > 0.05:  # 错误率超过 5%
        await StatisticsService.send_alert_notification(
            subject="API 错误率过高",
            message=f"最近 1 小时 API 错误率: {api_metrics.error_rate:.2%}"
        )
```

### 告警场景

- 服务健康检查失败（PostgreSQL、Redis、Celery 不可用）
- 磁盘空间不足（使用率超过 85%）
- API 错误率超过阈值（如 5%）
- 平均响应时间过高（如超过 500ms）

## 注意事项

### 1. 权限控制
- 所有统计接口必须使用 `get_current_admin` 进行管理员权限验证
- 不对外公开敏感的运营数据

### 2. 数据安全
- API 日志中的 IP 地址建议脱敏或加密存储
- 定期清理历史日志，避免数据泄露和存储膨胀

### 3. 性能考虑
- 统计接口建议配置速率限制，避免被滥用
- 大数据量场景下考虑使用分区表或归档历史数据

### 4. 依赖要求
- **Celery 统计**：需要 Celery worker 正常运行
- **日志记录**：需要 API 日志中间件已配置

### 5. 时区处理
- 所有时间统一使用 UTC
- 前端根据用户时区进行转换显示

## 故障排查

### 问题 1：仪表盘数据不更新

**检查 Redis 连接：**
```bash
redis-cli
> GET statistics:dashboard
> DEL statistics:dashboard  # 清除缓存
```

### 问题 2：趋势数据为空

**检查每日快照数据：**
```sql
SELECT * FROM daily_stats ORDER BY stat_date DESC LIMIT 7;
```

如果没有数据，手动执行快照任务：
```python
import asyncio
from app.modules.statistics.service import StatisticsService
asyncio.run(StatisticsService.record_daily_snapshot())
```

### 问题 3：API 日志未记录

**检查中间件配置：**
```python
# 在 main.py 中确认
setup_middlewares(app)  # 确保调用了这个函数
```

**查看错误日志：**
```bash
tail -f logs/app.log | grep "Failed to log API call"
```

### 问题 4：健康检查超时

增加超时时间或优化检查逻辑：
```python
# 在 service.py 中调整
async with asyncio.timeout(5):  # 改为 5 秒
    results = await asyncio.gather(...)
```

### 问题 5：健康检查返回 degraded

检查各子服务返回的 `detail` 字段，确认 Celery Worker、磁盘使用率等是否异常。

## 扩展功能

### 1. 导出统计报表

```python
import csv
from datetime import datetime

async def export_stats_csv(start_date, end_date):
    from app.modules.statistics.models import DailyStats
    
    stats = await DailyStats.filter(
        stat_date__gte=start_date,
        stat_date__lte=end_date
    ).order_by("stat_date")
    
    filename = f"stats_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '新增文章', '总阅读', '新增评论', '独立访客'])
        
        for stat in stats:
            writer.writerow([
                stat.stat_date,
                stat.new_articles,
                stat.total_views,
                stat.new_comments,
                stat.unique_visitors
            ])
    
    return filename
```

### 2. 实时数据推送

使用 WebSocket 推送实时统计数据：

```python
from fastapi import WebSocket
import asyncio

@router.websocket("/ws/statistics")
async def statistics_websocket(
    websocket: WebSocket,
    current_admin: AdminUser = Depends(get_current_admin)
):
    await websocket.accept()
    
    try:
        while True:
            dashboard_data = await StatisticsService.get_dashboard_data()
            await websocket.send_json({
                "type": "dashboard_update",
                "data": dashboard_data.model_dump()
            })
            await asyncio.sleep(5)  # 每 5 秒推送一次
    except Exception:
        await websocket.close()
```

### 3. 自定义统计指标

扩展 service 层添加自定义统计：

```python
@staticmethod
async def get_user_engagement_stats():
    """用户参与度统计"""
    # 评论活跃度
    active_commenters = await Comment.filter(
        created_at__gte=datetime.utcnow() - timedelta(days=7)
    ).distinct().count()
    
    # 平均文章阅读时长（需要额外埋点）
    # 内容互动率等
    
    return {
        "active_commenters": active_commenters,
        # 其他指标...
    }
```

## 测试验证

### 手动验证

启动服务后，通过 API 测试各功能：

```bash
# 1. 测试仪表盘数据
curl -X GET "http://localhost:8000/api/v1/admin/statistics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 测试系统健康检查
curl -X GET "http://localhost:8000/api/v1/admin/statistics/health" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 测试趋势数据
curl -X GET "http://localhost:8000/api/v1/admin/statistics/trends?metric=views&period=day" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python 脚本验证

```python
import asyncio
from app.modules.statistics.service import StatisticsService

async def test():
    # 测试仪表盘数据
    dashboard = await StatisticsService.get_dashboard_data()
    print(f"总文章数: {dashboard.total_articles}")
    
    # 测试系统健康
    health = await StatisticsService.check_system_health()
    print(f"系统状态: {health.overall_status}")

asyncio.run(test())
```
