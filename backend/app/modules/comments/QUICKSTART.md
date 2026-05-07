# 评论模块 - 快速启动指南

## 前置条件

1. 数据库迁移已完成（包含 comments 和 guest_identities 表）
2. Redis 服务已启动
3. 依赖已安装（markdown>=3.6）

## 启动步骤

### 1. 安装依赖

```bash
cd backend
uv pip install -e .
```

### 2. 配置环境变量

确保 `.env` 文件包含以下配置：

```env
# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=postgres://user:password@localhost:5432/blog_db
```

### 3. 运行数据库迁移

```bash
aerich upgrade
```

### 4. 初始化数据（可选）

#### 添加默认敏感词

```python
# 运行 Python 脚本或直接在数据库中执行
from app.modules.system.models import SensitiveWord

await SensitiveWord.create(word="测试敏感词", category="默认", is_active=True)
```

#### 配置评论审核模式

```python
from app.modules.system.models import SiteConfig

# 自动审核通过
await SiteConfig.create(
    key="comment_auto_approve",
    value="true",
    value_type="bool",
    description="评论是否自动通过审核"
)
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 测试

### 测试游客身份创建

```bash
curl http://localhost:8000/api/v1/guest/identity
```

预期返回：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "guest_token": "...",
    "nickname": null,
    "created_at": "2026-05-07T15:30:00"
  }
}
```

### 测试设置昵称

```bash
curl -X PUT http://localhost:8000/api/v1/guest/nickname \
  -H "Content-Type: application/json" \
  -b "guest_token=YOUR_GUEST_TOKEN" \
  -d '{"nickname":"测试用户"}'
```

### 测试提交评论

```bash
curl -X POST http://localhost:8000/api/v1/comments \
  -H "Content-Type: application/json" \
  -b "guest_token=YOUR_GUEST_TOKEN" \
  -d '{
    "article_id": 1,
    "content": "这是一条测试评论"
  }'
```

### 测试获取评论列表

```bash
curl http://localhost:8000/api/v1/articles/1/comments?page=1&page_size=20
```

### 测试管理员操作（需要认证）

```bash
# 获取评论列表
curl http://localhost:8000/api/v1/admin/comments?status=pending \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# 审核通过
curl -X POST http://localhost:8000/api/v1/admin/comments/1/action \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "reason": "内容合规"
  }'

# 管理员回复
curl -X POST http://localhost:8000/api/v1/admin/comments/1/reply \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "感谢您的反馈！"
  }'
```

### 测试 WebSocket（管理员端）

使用 WebSocket 客户端连接：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/admin/comments');

ws.onmessage = (event) => {
  console.log('收到消息:', event.data);
  // {"type": "new_comment", "comment_id": 123}
};
```

## 单元测试

运行测试：

```bash
cd backend
pytest tests/test_comments.py -v
```

## 常见问题

### Q: 评论提交后状态为 pending？

A: 检查 `site_configs` 表中的 `comment_auto_approve` 配置：
- `true`：自动通过审核
- `false`：需要管理员审核

### Q: 敏感词过滤不生效？

A: 检查以下几点：
1. Redis 是否正常运行
2. `sensitive_words` 表中是否有数据且 `is_active=true`
3. 清除 Redis 缓存：`redis-cli DEL sensitive_words:list`

### Q: 限流提示"评论过于频繁"？

A: 系统限制同一游客每分钟最多提交 5 条评论。等待 60 秒后重试。

### Q: WebSocket 连接断开？

A: 建议添加心跳机制或自动重连逻辑。

## 数据库索引优化

建议添加以下索引以提升性能：

```sql
-- 评论表索引
CREATE INDEX idx_comments_article_status ON comments(article_id, status);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_created ON comments(created_at DESC);

-- 游客身份表索引
CREATE INDEX idx_guest_token ON guest_identities(guest_token);
CREATE INDEX idx_guest_nickname ON guest_identities(nickname);
```

## 监控建议

1. **评论量监控**：监控每日评论提交量
2. **审核队列**：监控待审核评论数量
3. **限流触发**：监控限流触发次数
4. **WebSocket 连接数**：监控管理员 WebSocket 连接数
5. **敏感词命中**：监控敏感词拦截次数

## 下一步

- [ ] 配置邮件通知（评论被回复时通知）
- [ ] 添加评论点赞功能
- [ ] 实现评论举报机制
- [ ] 集成前端 Markdown 编辑器
- [ ] 添加表情支持
