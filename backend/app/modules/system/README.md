# 系统管理模块

## 功能

- **站点配置**: 字符串/整数/布尔/JSON 类型，Redis 缓存（5 分钟），公开/私有区分，批量更新
- **功能开关**: AI / 评论启停，Redis 缓存
- **敏感词**: CRUD、分类、启用/禁用、Redis 缓存（10 分钟）、批量导入
- **操作日志**: 管理员操作记录，按操作人/类型/时间查询，分页
- **管理员通知**: 站内通知模型，未读计数、列表、标记已读、全部已读

## API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/system/configs/public` | GET | 公开配置（无需认证） |
| `/admin/system/configs` | GET | 全部配置 |
| `/admin/system/configs/{key}` | PUT | 更新单个配置 |
| `/admin/system/configs/bulk` | POST | 批量更新配置 |
| `/admin/system/sensitive-words` | GET/POST | 敏感词列表/创建 |
| `/admin/system/sensitive-words/import` | POST | 批量导入 |
| `/admin/system/sensitive-words/{id}` | DELETE | 删除敏感词 |
| `/admin/system/sensitive-words/refresh-cache` | POST | 刷新缓存 |
| `/admin/system/logs` | GET | 操作日志（分页） |
| `/admin/system/notifications` | GET | 通知列表（分页） |
| `/admin/system/notifications/unread-count` | GET | 未读通知数 |
| `/admin/system/notifications/{id}/read` | PUT | 标记已读 |
| `/admin/system/notifications/read-all` | PUT | 全部已读 |
| `/admin/system/tasks` | GET/PUT/POST | 定时任务管理 |

## 默认配置项

| Key | 默认值 | 类型 | 公开 |
|---|---|---|---|
| `SITE_NAME` | 我的博客 | str | ✓ |
| `SITE_DESCRIPTION` | ... | str | ✓ |
| `SITE_KEYWORDS` | 博客,技术,分享 | str | ✓ |
| `SITE_AUTHOR` | 博主 | str | ✓ |
| `ICP_NUMBER` | — | str | ✓ |
| `COMMENT_ENABLED` | true | bool | ✓ |
| `AI_ENABLED` | true | bool | ✓ |
| `COMMENT_DAILY_LIMIT_PER_USER` | 2 | int | ✗ |
| `GUESTBOOK_DAILY_LIMIT_PER_USER` | 2 | int | ✗ |
| `ASSISTANT_GUEST_DAILY_LIMIT` | 3 | int | ✗ |
