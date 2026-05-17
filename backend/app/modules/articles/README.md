# 文章模块

## 功能

- 文章 CRUD、草稿编辑副本（不直接修改原文）
- 草稿/已发布/下架三态，定时发布
- 自动 Slug 生成（去重加后缀），SEO 字段
- 分类/标签管理（删除保护、排序）
- 阅读量统计（Redis 去重 24 小时同一 IP 只计一次）
- 全文搜索，封面图自动生成 16:9 缩略图和大图
- 文章状态变更时通知 N8N Webhook

## API 端点

**公开**:

| 端点 | 方法 | 说明 |
|---|---|---|
| `/articles` | GET | 文章列表（分页/分类/标签/搜索） |
| `/articles/{slug}` | GET | 文章详情（增加阅读量） |
| `/articles/search` | GET | 全文搜索 |
| `/categories` | GET | 分类列表（启用） |
| `/tags` | GET | 标签列表 |

**管理员**（需 Bearer Token）:

| 端点 | 说明 |
|---|---|
| `/admin/articles` | GET/POST：列表（含草稿）/创建 |
| `/admin/articles/{id}` | GET/PUT/DELETE：详情/更新/删除 |
| `/admin/articles/{id}/publish` | POST：发布 |
| `/admin/articles/{id}/unpublish` | POST：下架 |
| `/admin/articles/{id}/draft` | POST：创建/更新编辑副本 |
| `/admin/articles/{id}/publish-draft` | POST：从副本发布 |
| `/admin/categories` | GET/POST：列表/创建 |
| `/admin/categories/{id}` | PUT/DELETE：更新/删除 |
| `/admin/tags` | GET/POST：列表/创建 |
| `/admin/tags/{id}` | PUT/DELETE：更新/删除 |
