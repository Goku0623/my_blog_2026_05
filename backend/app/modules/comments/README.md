# 评论模块（Comments）

## 功能概述

评论模块提供完整的博客评论系统，支持游客匿名评论、楼中楼回复、敏感词过滤、评论审核和实时通知。

## 核心功能

### 1. 游客身份管理

- **自动创建游客身份**：访客首次访问时自动分配唯一的 `guest_token`
- **设置昵称**：游客可设置昵称（3-20字符，支持中文、字母、数字、下划线）
- **唯一性校验**：昵称在系统中唯一
- **封禁机制**：支持管理员封禁特定游客

### 2. 评论功能

- **Markdown 支持**：评论内容支持 Markdown 格式，自动渲染为 HTML
- **楼中楼回复**：支持一层嵌套回复（父评论 + 子回复）
- **敏感词过滤**：自动检测并拦截包含敏感词的评论
- **评论审核**：支持手动审核或自动通过两种模式
- **限流保护**：同一游客每分钟最多提交 5 条评论

### 3. 管理功能

- **评论管理**：查看所有状态的评论，支持多条件筛选
- **评论操作**：
  - `pin/unpin`：置顶/取消置顶
  - `approve`：通过审核
  - `hide`：隐藏评论
  - `delete`：删除评论
- **管理员回复**：管理员可直接回复评论
- **操作日志**：记录所有管理操作

### 4. 实时通知

- **WebSocket 推送**：新评论提交后实时通知所有在线管理员
- **连接管理**：自动处理连接异常和断线重连

## API 端点

### 公开端点

#### 获取游客身份
```http
GET /api/v1/guest/identity
```

返回游客身份信息，如果不存在则自动创建。同时设置 `guest_token` Cookie。

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "guest_token": "550e8400-e29b-41d4-a716-446655440000",
    "nickname": null,
    "created_at": "2026-05-07T15:30:00"
  }
}
```

#### 设置游客昵称
```http
PUT /api/v1/guest/nickname
```

**请求体：**
```json
{
  "nickname": "张三"
}
```

**昵称规则：**
- 长度：3-20 个字符
- 允许：中文、字母、数字、下划线
- 唯一性：系统内不能重复

#### 获取文章评论列表
```http
GET /api/v1/articles/{article_id}/comments?page=1&page_size=20
```

返回已审核通过的评论，按置顶状态和时间排序。自动构建树形结构（父评论 + 子回复）。

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1,
        "article_id": 10,
        "guest": {
          "id": 5,
          "guest_token": "...",
          "nickname": "张三",
          "created_at": "2026-05-07T15:00:00"
        },
        "parent_id": null,
        "reply_to_nickname": null,
        "content": "这篇文章写得真好！",
        "rendered_content": "<p>这篇文章写得真好！</p>",
        "status": "approved",
        "is_pinned": false,
        "admin_reply": null,
        "created_at": "2026-05-07T15:30:00",
        "replies": [
          {
            "id": 2,
            "parent_id": 1,
            "reply_to_nickname": "张三",
            "content": "我也这么觉得",
            "...": "..."
          }
        ]
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

#### 提交评论
```http
POST /api/v1/comments
```

**请求体：**
```json
{
  "article_id": 10,
  "parent_id": null,
  "content": "这是我的评论内容"
}
```

**参数说明：**
- `article_id`：文章 ID（必填）
- `parent_id`：父评论 ID（可选，回复时填写）
- `content`：评论内容（1-2000 字符，支持 Markdown）

**限制：**
- 文章必须开启评论功能
- 游客不能被封禁
- 不包含敏感词
- 限流：每分钟最多 5 条

### 管理员端点

#### 获取评论管理列表
```http
GET /api/v1/admin/comments?status=pending&page=1&page_size=20
```

**查询参数：**
- `status`：评论状态（pending/approved/hidden/deleted）
- `article_id`：文章 ID
- `keyword`：关键词搜索
- `page`：页码
- `page_size`：每页数量

#### 执行评论操作
```http
POST /api/v1/admin/comments/{comment_id}/action
```

**请求体：**
```json
{
  "action": "approve",
  "reason": "内容合规"
}
```

**操作类型：**
- `pin`：置顶
- `unpin`：取消置顶
- `approve`：通过审核
- `hide`：隐藏
- `delete`：删除

#### 管理员回复评论
```http
POST /api/v1/admin/comments/{comment_id}/reply
```

**请求体：**
```json
{
  "content": "感谢您的反馈！"
}
```

#### WebSocket 实时通知
```http
WS /api/v1/ws/admin/comments
```

管理员建立 WebSocket 连接后，每当有新评论提交时会收到通知：

```json
{
  "type": "new_comment",
  "comment_id": 123
}
```

## 数据模型

### GuestIdentity（游客身份）

```python
{
  "id": int,
  "guest_token": str,  # 唯一标识
  "nickname": str | null,  # 昵称
  "ip_address": str,
  "user_agent": str,
  "is_banned": bool,  # 是否被封禁
  "ban_reason": str | null,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Comment（评论）

```python
{
  "id": int,
  "article_id": int,
  "guest_id": int,
  "parent_id": int | null,  # 父评论 ID
  "reply_to_nickname": str | null,  # 回复对象昵称
  "content": str,  # 原始内容（Markdown）
  "rendered_content": str,  # 渲染后的 HTML
  "status": str,  # pending/approved/hidden/deleted
  "is_pinned": bool,  # 是否置顶
  "admin_reply": str | null,  # 管理员回复
  "ip_address": str,
  "created_at": datetime,
  "updated_at": datetime
}
```

## 敏感词管理

敏感词存储在 `SensitiveWord` 表中，并通过 Redis 缓存（缓存时间 1 小时）。

### 配置敏感词

在数据库中添加敏感词记录：

```sql
INSERT INTO sensitive_words (word, category, is_active) 
VALUES ('敏感词', '政治', true);
```

系统会自动：
1. 从数据库加载所有活跃的敏感词
2. 缓存到 Redis（key: `sensitive_words:list`）
3. 评论提交时实时检测

## 评论审核配置

通过 `SiteConfig` 表配置评论审核模式：

```sql
INSERT INTO site_configs (key, value, value_type, description) 
VALUES ('comment_auto_approve', 'true', 'bool', '评论是否自动通过审核');
```

- `true`：新评论自动通过审核（status = approved）
- `false`：新评论需要管理员审核（status = pending）

配置会缓存 5 分钟（key: `site_config:comment_auto_approve`）。

## 使用示例

### 前端集成示例

#### 1. 初始化游客身份

```javascript
async function initGuestIdentity() {
  const response = await fetch('/api/v1/guest/identity');
  const { data } = await response.json();
  localStorage.setItem('guest_token', data.guest_token);
  return data;
}
```

#### 2. 设置昵称

```javascript
async function setNickname(nickname) {
  const response = await fetch('/api/v1/guest/nickname', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nickname }),
    credentials: 'include'
  });
  return await response.json();
}
```

#### 3. 加载评论列表

```javascript
async function loadComments(articleId, page = 1) {
  const response = await fetch(
    `/api/v1/articles/${articleId}/comments?page=${page}&page_size=20`
  );
  const { data } = await response.json();
  return data;
}
```

#### 4. 提交评论

```javascript
async function submitComment(articleId, content, parentId = null) {
  const response = await fetch('/api/v1/comments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      article_id: articleId,
      parent_id: parentId,
      content
    }),
    credentials: 'include'
  });
  return await response.json();
}
```

#### 5. 管理员 WebSocket 连接

```javascript
function connectAdminWebSocket() {
  const ws = new WebSocket('ws://localhost:8000/api/v1/ws/admin/comments');
  
  ws.onopen = () => {
    console.log('WebSocket 已连接');
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'new_comment') {
      showNewCommentNotification(message.comment_id);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket 已断开，3秒后重连');
    setTimeout(connectAdminWebSocket, 3000);
  };
}
```

## 依赖项

模块依赖以下 Python 包：

- `markdown>=3.6`：Markdown 渲染
- `redis>=5.0.4`：缓存和限流
- `tortoise-orm[asyncpg]>=0.21.0`：数据库 ORM

确保在 `pyproject.toml` 中包含这些依赖。

## 性能优化建议

1. **敏感词缓存**：敏感词列表缓存 1 小时，减少数据库查询
2. **评论分页**：建议每页显示 20 条评论
3. **WebSocket 心跳**：建议添加心跳机制保持连接
4. **数据库索引**：确保以下字段建立索引：
   - `comments.article_id`
   - `comments.status`
   - `comments.parent_id`
   - `comments.created_at`
   - `guest_identities.guest_token`
   - `guest_identities.nickname`

## 安全建议

1. **XSS 防护**：前端渲染 HTML 时需要使用安全的 HTML 渲染库
2. **限流保护**：评论限流使用 Redis 滑动窗口，防止刷评论
3. **IP 封禁**：可根据 IP 地址批量封禁恶意游客
4. **内容审核**：敏感内容建议开启人工审核
5. **昵称验证**：严格验证昵称格式，防止注入攻击

## 故障排查

### 评论提交失败

1. 检查文章是否允许评论（`allow_comment = true`）
2. 检查游客是否被封禁
3. 检查是否触发限流（每分钟 5 条）
4. 检查是否包含敏感词

### WebSocket 连接失败

1. 确认服务器支持 WebSocket 协议
2. 检查防火墙和代理配置
3. 确认管理员认证 token 有效

### 敏感词不生效

1. 检查 Redis 缓存是否正常
2. 确认敏感词 `is_active = true`
3. 手动清除缓存：`redis-cli DEL sensitive_words:list`

## 扩展建议

1. **邮件通知**：评论被回复时发送邮件通知
2. **点赞功能**：为评论添加点赞统计
3. **举报机制**：允许用户举报不当评论
4. **富文本编辑器**：前端集成 Markdown 编辑器
5. **表情支持**：支持 emoji 表情
6. **图片上传**：允许评论中上传图片（需配合文件上传模块）
