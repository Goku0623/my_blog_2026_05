# 系统管理模块（System Module）

## 概述

系统管理模块提供站点配置管理、功能开关、敏感词过滤、操作日志记录和定时任务管理等核心功能。

## 功能清单

### 1. 站点配置管理

- 支持多种配置类型（字符串、整数、布尔值、JSON）
- Redis 缓存加速配置读取（TTL=5分钟）
- 公开配置/私有配置区分
- 批量更新配置

### 2. 功能开关

- 评论功能开关（COMMENT_ENABLED）
- 聊天室功能开关（CHATROOM_ENABLED）
- AI功能开关（AI_ENABLED）
- 自动缓存到 Redis

### 3. 敏感词管理

- 敏感词增删查
- Redis 缓存（TTL=10分钟）
- 支持分类管理
- 启用/禁用状态

### 4. 操作日志

- 记录管理员操作
- 支持按操作人、操作类型、时间范围查询
- 分页查询

### 5. 定时任务管理

- 任务列表查询
- 更新任务配置（启用状态、Cron表达式）
- 手动触发任务执行

## 数据模型

### SiteConfig

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| key | varchar(100) | 配置键（唯一） |
| value | text | 配置值 |
| value_type | varchar(20) | 值类型（str/int/bool/json） |
| description | text | 配置说明 |
| is_public | boolean | 是否公开（前端可读） |
| updated_at | datetime | 更新时间 |

### SensitiveWord

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| word | varchar(100) | 敏感词（唯一） |
| category | varchar(50) | 分类 |
| is_active | boolean | 是否启用 |
| created_at | datetime | 创建时间 |

### OperationLog

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| operator | varchar(50) | 操作人 |
| action | varchar(100) | 操作类型 |
| target_type | varchar(50) | 目标类型 |
| target_id | int | 目标ID |
| detail | text | 操作详情 |
| ip_address | varchar(50) | IP地址 |
| result | varchar(20) | 操作结果（success/failure） |
| created_at | datetime | 创建时间 |

### ScheduledTask

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | varchar(100) | 任务名称（唯一） |
| task_path | varchar(200) | 任务路径 |
| cron_expression | varchar(100) | Cron表达式 |
| is_active | boolean | 是否启用 |
| last_run_at | datetime | 上次运行时间 |
| next_run_at | datetime | 下次运行时间 |
| last_result | text | 上次运行结果 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## API 接口

### 公开接口（无需认证）

#### GET /system/configs/public

获取公开配置（供前端读取站点基本信息）

**Response:**
```json
{
  "code": 0,
  "message": "获取公开配置成功",
  "data": {
    "SITE_NAME": "博客系统",
    "SITE_DESCRIPTION": "一个现代化的博客系统",
    "SITE_LOGO": "https://example.com/logo.png",
    "ICP_NUMBER": "京ICP备xxxxxxxx号"
  }
}
```

### 管理员接口（需要认证）

#### GET /system/admin/configs

获取所有配置

**Query Parameters:**
- `is_public_only` (boolean): 仅返回公开配置

**Response:**
```json
{
  "code": 0,
  "message": "获取配置列表成功",
  "data": [
    {
      "id": 1,
      "key": "SITE_NAME",
      "value": "博客系统",
      "value_type": "str",
      "description": "站点名称",
      "is_public": true,
      "updated_at": "2026-05-07T10:00:00"
    }
  ]
}
```

#### PUT /system/admin/configs/{key}

更新单个配置

**Request Body:**
```json
{
  "value": "新的配置值"
}
```

**Response:**
```json
{
  "code": 0,
  "message": "更新配置成功",
  "data": {
    "id": 1,
    "key": "SITE_NAME",
    "value": "新的配置值",
    "value_type": "str",
    "description": "站点名称",
    "is_public": true,
    "updated_at": "2026-05-07T11:00:00"
  }
}
```

#### POST /system/admin/configs/bulk

批量更新配置

**Request Body:**
```json
{
  "configs": [
    {"key": "SITE_NAME", "value": "新站点名称"},
    {"key": "COMMENT_ENABLED", "value": "false"}
  ]
}
```

**Response:**
```json
{
  "code": 0,
  "message": "批量更新配置成功",
  "data": [...]
}
```

#### GET /system/admin/sensitive-words

获取敏感词列表

**Query Parameters:**
- `category` (string): 分类筛选
- `is_active` (boolean): 启用状态筛选

**Response:**
```json
{
  "code": 0,
  "message": "获取敏感词列表成功",
  "data": [
    {
      "id": 1,
      "word": "敏感词",
      "category": "政治",
      "is_active": true,
      "created_at": "2026-05-07T10:00:00"
    }
  ]
}
```

#### POST /system/admin/sensitive-words

创建敏感词

**Request Body:**
```json
{
  "word": "敏感词",
  "category": "政治"
}
```

**Response:**
```json
{
  "code": 0,
  "message": "创建敏感词成功",
  "data": {
    "id": 1,
    "word": "敏感词",
    "category": "政治",
    "is_active": true,
    "created_at": "2026-05-07T10:00:00"
  }
}
```

#### DELETE /system/admin/sensitive-words/{word_id}

删除敏感词

**Response:**
```json
{
  "code": 0,
  "message": "删除敏感词成功",
  "data": null
}
```

#### POST /system/admin/sensitive-words/refresh-cache

刷新敏感词缓存

**Response:**
```json
{
  "code": 0,
  "message": "刷新敏感词缓存成功",
  "data": null
}
```

#### GET /system/admin/logs

查询操作日志

**Query Parameters:**
- `operator` (string): 操作人筛选
- `action` (string): 操作类型筛选
- `start_date` (datetime): 开始时间
- `end_date` (datetime): 结束时间
- `page` (int): 页码（默认1）
- `page_size` (int): 每页数量（默认20，最大100）

**Response:**
```json
{
  "code": 0,
  "message": "获取操作日志成功",
  "data": {
    "items": [
      {
        "id": 1,
        "operator": "admin",
        "action": "update_config",
        "target_type": "site_config",
        "target_id": 1,
        "detail": "更新配置 SITE_NAME: 旧值 -> 新值",
        "ip_address": "192.168.1.1",
        "result": "success",
        "created_at": "2026-05-07T10:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

#### GET /system/admin/tasks

获取定时任务列表

**Response:**
```json
{
  "code": 0,
  "message": "获取定时任务列表成功",
  "data": [
    {
      "id": 1,
      "name": "clean_old_logs",
      "task_path": "app.tasks.clean_old_logs",
      "cron_expression": "0 2 * * *",
      "is_active": true,
      "last_run_at": "2026-05-07T02:00:00",
      "next_run_at": "2026-05-08T02:00:00",
      "last_result": "成功清理1000条过期日志"
    }
  ]
}
```

#### PUT /system/admin/tasks/{task_id}

更新定时任务配置

**Request Body:**
```json
{
  "is_active": false,
  "cron_expression": "0 3 * * *"
}
```

**Response:**
```json
{
  "code": 0,
  "message": "更新定时任务成功",
  "data": {...}
}
```

#### POST /system/admin/tasks/{task_id}/trigger

手动触发定时任务

**Response:**
```json
{
  "code": 0,
  "message": "触发定时任务成功",
  "data": {
    "message": "任务 clean_old_logs 已触发执行"
  }
}
```

## 服务层接口

### SiteConfigService

```python
# 获取所有配置
await SiteConfigService.get_all_configs(is_public_only=False)

# 获取单个配置（带缓存）
value = await SiteConfigService.get_config("SITE_NAME")

# 更新配置（删除缓存 + 记录日志）
await SiteConfigService.update_config("SITE_NAME", "新值", admin)

# 批量更新配置
await SiteConfigService.bulk_update_configs([{"key": "...", "value": "..."}], admin)

# 获取公开配置（前端）
configs_dict = await SiteConfigService.get_public_configs()

# 初始化默认配置（应用启动时调用）
await SiteConfigService.init_default_configs()
```

### FeatureSwitchService

```python
# 检查功能开关（带缓存）
enabled = await FeatureSwitchService.is_comment_enabled()
enabled = await FeatureSwitchService.is_chatroom_enabled()
enabled = await FeatureSwitchService.is_ai_enabled()
```

### SensitiveWordService

```python
# 创建敏感词
word = await SensitiveWordService.create_sensitive_word("敏感词", "分类")

# 删除敏感词
await SensitiveWordService.delete_sensitive_word(word_id)

# 查询敏感词列表
words = await SensitiveWordService.list_sensitive_words(category="政治")

# 获取缓存的敏感词集合（用于过滤）
word_set = await SensitiveWordService.get_sensitive_words_cached()

# 刷新敏感词缓存
await SensitiveWordService.refresh_sensitive_words_cache()
```

### OperationLogService

```python
# 记录操作日志（异步）
await OperationLogService.log_operation(
    operator="admin",
    action="update_config",
    target_type="site_config",
    target_id=1,
    detail="操作详情",
    ip="192.168.1.1",
    result="success"
)

# 查询日志（分页）
logs, total = await OperationLogService.query_logs(
    operator="admin",
    action="update_config",
    start_date=datetime(...),
    end_date=datetime(...),
    page=1,
    page_size=20
)
```

### ScheduledTaskService

```python
# 获取所有任务
tasks = await ScheduledTaskService.list_tasks()

# 更新任务配置
task = await ScheduledTaskService.update_task(
    task_id=1,
    is_active=True,
    cron_expression="0 3 * * *"
)

# 手动触发任务
result = await ScheduledTaskService.trigger_task_manually("clean_old_logs")
```

## Redis 缓存策略

### 配置缓存

- **Key 格式**: `config:{key}`
- **TTL**: 300秒（5分钟）
- **更新策略**: 写入数据库后立即删除缓存

### 敏感词缓存

- **Key**: `sensitive_words`
- **TTL**: 600秒（10分钟）
- **数据格式**: JSON数组
- **更新策略**: 增删敏感词后立即刷新缓存

## 默认配置项

系统启动时会自动初始化以下配置：

| 配置键 | 默认值 | 类型 | 说明 | 公开 |
|--------|--------|------|------|------|
| SITE_NAME | 博客系统 | str | 站点名称 | ✓ |
| SITE_DESCRIPTION | 一个现代化的博客系统 | str | 站点描述 | ✓ |
| SITE_LOGO | 空 | str | 站点Logo URL | ✓ |
| ICP_NUMBER | 空 | str | ICP备案号 | ✓ |
| COMMENT_ENABLED | true | bool | 评论功能开关 | ✗ |
| CHATROOM_ENABLED | true | bool | 聊天室功能开关 | ✗ |
| AI_ENABLED | true | bool | AI功能开关 | ✗ |
| COMMENT_NEED_REVIEW | true | bool | 评论需要审核 | ✗ |
| COMMENT_RATE_LIMIT | 5 | int | 评论速率限制（每分钟） | ✗ |
| CHAT_RATE_LIMIT | 3 | int | 聊天速率限制（每10秒） | ✗ |
| AI_API_KEY | 空 | str | AI API密钥 | ✗ |
| AI_BASE_URL | 空 | str | AI API地址 | ✗ |
| AI_MODEL | 空 | str | AI模型名称 | ✗ |
| WEATHER_API_KEY | 空 | str | 天气API密钥 | ✗ |
| N8N_SECRET | 空 | str | N8N Webhook密钥 | ✗ |
| ADMIN_EMAIL | 空 | str | 管理员邮箱 | ✗ |

## 使用示例

### 在其他模块中使用功能开关

```python
from app.modules.system.service import FeatureSwitchService

async def create_comment(...):
    if not await FeatureSwitchService.is_comment_enabled():
        raise BadRequestException("评论功能已关闭")
    # 创建评论逻辑...
```

### 在其他模块中使用敏感词过滤

```python
from app.modules.system.service import SensitiveWordService

async def check_content(content: str) -> bool:
    sensitive_words = await SensitiveWordService.get_sensitive_words_cached()
    for word in sensitive_words:
        if word in content:
            return False
    return True
```

### 记录操作日志

```python
from app.modules.system.service import OperationLogService

async def delete_article(article_id: int, admin: AdminUser):
    # 删除文章逻辑...
    await OperationLogService.log_operation(
        operator=admin.username,
        action="delete_article",
        target_type="article",
        target_id=article_id,
        detail=f"删除文章ID={article_id}",
        ip=get_client_ip(request),
        result="success"
    )
```

## 应用启动初始化

在应用启动时需要初始化默认配置：

```python
from app.modules.system.service import SiteConfigService

@app.on_event("startup")
async def startup_event():
    await SiteConfigService.init_default_configs()
```

## 注意事项

1. **缓存一致性**: 更新配置后会自动删除 Redis 缓存，下次读取时重新加载
2. **敏感词过滤**: 敏感词缓存会定期过期，建议在增删操作后手动刷新缓存
3. **操作日志**: 日志记录是异步的，不影响主流程性能
4. **定时任务**: 需要配合 Celery 或其他任务调度器使用
5. **公开配置**: 前端可直接访问 `/system/configs/public` 获取站点基本信息，无需认证

## 依赖关系

- **Redis**: 用于配置和敏感词缓存
- **Tortoise ORM**: 数据库操作
- **FastAPI**: API 路由
- **Pydantic**: 数据校验

## 错误处理

所有接口统一使用 `app.common.exceptions` 中的异常：
- `NotFoundException`: 资源不存在（404）
- `BadRequestException`: 请求参数错误（400）
- `UnauthorizedException`: 未认证（401）
- `ForbiddenException`: 无权限（403）

## 扩展建议

1. **配置历史**: 记录配置修改历史，支持回滚
2. **敏感词智能检测**: 使用 AC 自动机或前缀树优化敏感词匹配性能
3. **操作日志导出**: 支持导出为 CSV/Excel
4. **定时任务监控**: 集成 Sentry 或其他监控工具，任务失败时发送告警
5. **配置分组**: 将配置按模块分组管理
6. **配置加密**: 敏感配置（如API密钥）加密存储
