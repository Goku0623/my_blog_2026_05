# 文章模块 (Articles Module)

完整的文章管理系统，包含文章、分类、标签的 CRUD 操作，以及搜索、阅读量统计等功能。

## 功能特性

### 📝 文章管理
- **状态管理**: draft（草稿）、published（已发布）、unpublished（已下架）
- **自动生成 Slug**: 从标题自动生成唯一的 URL slug
- **SEO 优化**: 支持自定义 SEO 标题、描述、关键词
- **多对多标签**: 灵活的标签系统
- **分类管理**: 文章可关联分类
- **阅读量统计**: Redis 去重（24小时内同一IP只计一次）
- **全文搜索**: 标题、内容、摘要搜索

### 📂 分类管理
- **排序**: 支持自定义排序
- **启用/禁用**: 可控制分类显示状态
- **删除保护**: 有文章关联时无法删除

### 🏷️ 标签管理
- **颜色标记**: 每个标签可设置颜色
- **删除保护**: 有文章关联时无法删除

## 数据模型

### Article (文章)
```python
- id: 主键
- title: 标题
- slug: URL slug（唯一）
- summary: 摘要
- content: 正文内容
- rendered_content: 渲染后的内容
- status: draft/published/unpublished
- category_id: 分类ID（可选）
- cover_image: 封面图
- view_count: 阅读量
- is_featured: 是否精选
- allow_comment: 是否允许评论
- seo_title: SEO标题
- seo_description: SEO描述
- seo_keywords: SEO关键词
- published_at: 发布时间
- created_at: 创建时间
- updated_at: 更新时间
```

### Category (分类)
```python
- id: 主键
- name: 名称
- slug: URL slug（唯一）
- description: 描述
- sort_order: 排序
- is_active: 是否启用
- created_at: 创建时间
- updated_at: 更新时间
```

### Tag (标签)
```python
- id: 主键
- name: 名称
- slug: URL slug（唯一）
- color: 颜色（如 #FF0000）
- created_at: 创建时间
- updated_at: 更新时间
```

### ArticleTag (文章-标签关联)
```python
- id: 主键
- article_id: 文章ID
- tag_id: 标签ID
```

### ArticleView (阅读记录)
```python
- id: 主键
- article_id: 文章ID
- ip_address: IP地址
- user_agent: User Agent
- viewed_at: 阅读时间
```

## API 端点

### 公开接口（无需认证）

#### 1. GET /api/v1/articles
获取文章列表（仅返回已发布）

**查询参数:**
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10，最大 100）
- `category_id`: 分类ID过滤（可选）
- `tag_id`: 标签ID过滤（可选）
- `keyword`: 关键词搜索（可选）

**响应示例:**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [...],
    "total": 50,
    "page": 1,
    "page_size": 10,
    "total_pages": 5
  }
}
```

---

#### 2. GET /api/v1/articles/{slug}
获取文章详情（自动增加阅读量）

**路径参数:**
- `slug`: 文章 slug

**响应示例:**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "title": "FastAPI 快速入门指南",
    "slug": "fastapi-kuai-su-ru-men-zhi-nan",
    "summary": "学习如何使用 FastAPI...",
    "content": "# FastAPI 快速入门\n...",
    "status": "published",
    "category": {
      "id": 1,
      "name": "技术分享",
      "slug": "tech"
    },
    "tags": [
      {"id": 1, "name": "Python", "slug": "python", "color": "#3776AB"}
    ],
    "view_count": 123,
    "published_at": "2026-05-07T10:00:00",
    "created_at": "2026-05-07T09:00:00"
  }
}
```

**注意:** 同一IP在24小时内多次访问只计一次阅读量

---

#### 3. GET /api/v1/articles/search
全文搜索

**查询参数:**
- `keyword`: 搜索关键词（必填）
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10）

**响应示例:**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [...],
    "total": 15,
    "page": 1,
    "page_size": 10,
    "total_pages": 2
  }
}
```

---

#### 4. GET /api/v1/categories
获取分类列表（仅返回启用的）

**响应示例:**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": 1,
      "name": "技术分享",
      "slug": "tech",
      "description": "技术相关文章",
      "sort_order": 1,
      "is_active": true
    }
  ]
}
```

---

#### 5. GET /api/v1/tags
获取标签列表

**响应示例:**
```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": 1,
      "name": "Python",
      "slug": "python",
      "color": "#3776AB"
    }
  ]
}
```

---

### 管理员接口（需要认证）

所有管理员接口都需要在请求头中携带：
```
Authorization: Bearer <access_token>
```

#### 6. GET /api/v1/admin/articles
获取文章列表（可见所有状态）

**查询参数:**
- `page`: 页码
- `page_size`: 每页数量
- `status_filter`: 状态过滤（draft/published/unpublished）
- `category_id`: 分类过滤
- `tag_id`: 标签过滤
- `keyword`: 关键词搜索

---

#### 7. POST /api/v1/admin/articles
创建文章

**请求体:**
```json
{
  "title": "FastAPI 快速入门指南",
  "summary": "学习如何使用 FastAPI 构建高性能的 Web API",
  "content": "# FastAPI 快速入门\n\n...",
  "category_id": 1,
  "tag_ids": [1, 2],
  "status": "draft",
  "cover_image": "https://example.com/cover.jpg",
  "allow_comment": true,
  "seo_title": "FastAPI 快速入门 - 完整指南",
  "seo_description": "详细的 FastAPI 入门教程",
  "seo_keywords": "FastAPI, Python, Web API"
}
```

**说明:**
- `slug` 会自动从 `title` 生成
- 如果 slug 重复，会自动添加数字后缀

---

#### 8. GET /api/v1/admin/articles/{id}
获取单篇文章（含草稿）

---

#### 9. PUT /api/v1/admin/articles/{id}
更新文章

**请求体:** 同创建，所有字段都是可选的

---

#### 10. DELETE /api/v1/admin/articles/{id}
删除文章

**查询参数:**
- `hard_delete`: 是否硬删除（默认 false）

**说明:**
- 软删除：将 status 设为 "deleted"，数据保留
- 硬删除：彻底删除文章及关联数据

---

#### 11. POST /api/v1/admin/articles/{id}/publish
发布文章

**说明:**
- 将 status 改为 "published"
- 自动设置 published_at 为当前时间（如果之前未设置）

---

#### 12. POST /api/v1/admin/articles/{id}/unpublish
下架文章

**说明:**
- 将 status 改为 "unpublished"

---

#### 13. POST /api/v1/admin/categories
创建分类

**请求体:**
```json
{
  "name": "技术分享",
  "slug": "tech",
  "description": "技术相关文章",
  "sort_order": 1,
  "is_active": true
}
```

---

#### 14. PUT /api/v1/admin/categories/{id}
更新分类

---

#### 15. DELETE /api/v1/admin/categories/{id}
删除分类

**说明:** 如果有文章使用该分类，删除会失败

---

#### 16. POST /api/v1/admin/tags
创建标签

**请求体:**
```json
{
  "name": "Python",
  "slug": "python",
  "color": "#3776AB"
}
```

---

#### 17. PUT /api/v1/admin/tags/{id}
更新标签

---

#### 18. DELETE /api/v1/admin/tags/{id}
删除标签

**说明:** 如果有文章使用该标签，删除会失败

---

## Service 层方法

### CategoryService

#### create_category(data: CategoryCreate) -> Category
创建分类，自动检查 slug 唯一性

#### update_category(category_id, data: CategoryUpdate) -> Category
更新分类

#### delete_category(category_id) -> None
删除分类（带保护检查）

#### list_categories(is_active_only=False) -> List[Category]
获取分类列表

#### get_category_by_id(category_id) -> Optional[Category]
根据ID获取分类

---

### TagService

#### create_tag(data: TagCreate) -> Tag
创建标签

#### update_tag(tag_id, data: TagUpdate) -> Tag
更新标签

#### delete_tag(tag_id) -> None
删除标签（带保护检查）

#### list_tags() -> List[Tag]
获取所有标签

#### get_tag_by_id(tag_id) -> Optional[Tag]
根据ID获取标签

---

### ArticleService

#### create_article(data: ArticleCreate, admin_id: int) -> Article
创建文章
- 自动生成唯一 slug
- 处理标签关联

#### update_article(article_id, data: ArticleUpdate) -> Article
更新文章
- 支持更新标签（删除旧关联，创建新关联）

#### publish_article(article_id) -> Article
发布文章
- 设置 status = "published"
- 设置 published_at（如果未设置）

#### unpublish_article(article_id) -> Article
下架文章

#### delete_article(article_id, hard_delete=False) -> None
删除文章
- 软删除：status = "deleted"
- 硬删除：彻底删除数据

#### list_articles(...) -> Dict
分页列表
- 支持状态、分类、标签、关键词过滤
- 管理员可见所有状态，公开接口只返回 published

#### get_article_by_slug(slug, is_admin=False) -> Optional[Article]
根据 slug 获取文章

#### increment_view_count(article_id, ip, user_agent) -> bool
增加阅读量
- Redis 去重（key: `view:{article_id}:{ip}`，TTL: 24h）
- 使用 F 表达式原子性更新计数
- 创建阅读记录

#### search_articles(keyword, page, page_size) -> Dict
全文搜索（只搜索已发布文章）

---

## 使用示例

### 1. 创建分类和标签

```bash
# 登录获取 token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}' \
  | jq -r '.data.access_token')

# 创建分类
curl -X POST http://localhost:8000/api/v1/admin/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术分享",
    "slug": "tech",
    "description": "技术相关文章"
  }'

# 创建标签
curl -X POST http://localhost:8000/api/v1/admin/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "slug": "python",
    "color": "#3776AB"
  }'
```

### 2. 创建并发布文章

```bash
# 创建草稿
ARTICLE_ID=$(curl -X POST http://localhost:8000/api/v1/admin/articles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 快速入门指南",
    "summary": "学习如何使用 FastAPI",
    "content": "# FastAPI 入门\n\n...",
    "category_id": 1,
    "tag_ids": [1],
    "status": "draft"
  }' | jq -r '.data.id')

# 发布文章
curl -X POST http://localhost:8000/api/v1/admin/articles/$ARTICLE_ID/publish \
  -H "Authorization: Bearer $TOKEN"
```

### 3. 获取文章列表

```bash
# 公开接口（只返回已发布）
curl http://localhost:8000/api/v1/articles?page=1&page_size=10

# 管理员接口（可见所有状态）
curl http://localhost:8000/api/v1/admin/articles?page=1&status_filter=draft \
  -H "Authorization: Bearer $TOKEN"
```

### 4. 搜索文章

```bash
curl "http://localhost:8000/api/v1/articles/search?keyword=FastAPI&page=1"
```

### 5. 获取文章详情

```bash
curl http://localhost:8000/api/v1/articles/fastapi-kuai-su-ru-men-zhi-nan
```

---

## 测试

运行自动化测试：

```bash
cd backend
uv run python test_articles.py
```

测试包含：
1. 登录
2. 创建分类
3. 创建标签
4. 创建文章（草稿）
5. 发布文章
6. 获取公开文章列表
7. 获取文章详情（自动增加阅读量）
8. 搜索文章
9. 更新文章
10. 列出分类和标签

---

## 注意事项

### 阅读量去重
- 使用 Redis 存储访问记录
- Key 格式: `view:{article_id}:{ip_address}`
- TTL: 24 小时
- 同一IP在24小时内多次访问只计一次

### Slug 生成
- 从标题自动生成（中文转拼音 slug）
- 自动检查唯一性
- 如有重复，添加数字后缀（如 `article-1`、`article-2`）

### 软删除 vs 硬删除
- **软删除**（默认）：status 设为 "deleted"，数据保留，可恢复
- **硬删除**：彻底删除文章、标签关联、阅读记录

### 分类/标签删除保护
- 有文章关联时无法删除
- 返回 400 错误，提示文章数量

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求错误（如 slug 重复、分类被使用） |
| 401 | 未授权（需要登录） |
| 404 | 资源不found（文章/分类/标签不存在） |
| 500 | 服务器错误 |

---

## 依赖

- `tortoise-orm`: ORM
- `redis`: 阅读量去重
- `app.common.utils.generate_slug`: Slug 生成工具

---

## 扩展建议

1. **Markdown 渲染**: 可在 `create_article`/`update_article` 时自动渲染 `rendered_content`
2. **文章归档**: 按年月归档
3. **相关文章推荐**: 基于标签相似度
4. **草稿自动保存**: 前端定时保存草稿
5. **版本历史**: 记录文章修改历史
6. **批量操作**: 批量发布、删除、修改分类等
