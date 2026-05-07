# 聊天室模块（Chatroom）

## 功能概述

聊天室模块提供基于 WebSocket 的实时聊天功能，支持游客匿名聊天、在线状态管理、消息撤回、用户封禁和管理员管控。

## 核心功能

### 1. 实时聊天

- **WebSocket 连接**：基于 FastAPI WebSocket 实现双向实时通信
- **游客身份**：复用评论模块的游客身份系统
- **消息类型**：支持普通消息、系统消息、公告
- **消息长度限制**：单条消息最多 200 字符
- **消息持久化**：所有消息保存到数据库

### 2. 在线状态管理

- **Redis 状态追踪**：每个在线用户在 Redis 中维持状态（TTL=65s）
- **心跳机制**：每 30 秒自动发送 ping 保持连接活跃
- **在线统计**：实时获取在线人数和在线用户列表
- **自动清理**：连接断开时自动清理 Redis 状态

### 3. 消息管控

- **消息撤回**：管理员可撤回任意消息
- **历史清空**：管理员可清空聊天历史
- **敏感词过滤**：自动检测并拦截敏感内容
- **限流保护**：每个游客 10 秒内最多发送 3 条消息

### 4. 用户管理

- **封禁功能**：支持永久封禁或限时封禁（按分钟）
- **踢出功能**：临时踢出用户但不封禁
- **封禁检查**：连接时和消息发送时检查封禁状态
- **自动断连**：被封禁或踢出的用户自动断开连接

### 5. 管理员功能

- **管理员 WebSocket**：独立的管理员 WebSocket 连接
- **实时管控**：通过 WebSocket 或 HTTP 接口执行管理操作
- **操作类型**：
  - `recall`：撤回消息
  - `ban`：封禁用户
  - `kick`：踢出用户
  - `announcement`：发送公告
  - `clear_history`：清空历史

## API 端点

### 公开端点

#### 获取聊天历史
```http
GET /api/v1/chatroom/history?limit=50&before_id=100
```

**查询参数：**
- `limit`：返回消息数量（1-100，默认 50）
- `before_id`：获取此消息 ID 之前的消息（用于分页）

**响应示例：**
```json
{
  "messages": [
    {
      "id": 1,
      "sender_nickname": "张三",
      "message_type": "text",
      "content": "大家好！",
      "is_recalled": false,
      "created_at": "2026-05-07T15:30:00"
    }
  ],
  "total": 1
}
```

#### 获取在线信息
```http
GET /api/v1/chatroom/online
```

**响应示例：**
```json
{
  "online_count": 5,
  "online_list": [
    {
      "guest_token": "abc123",
      "nickname": "张三"
    }
  ]
}
```

#### 游客聊天室 WebSocket
```http
WS /api/v1/chatroom/ws/chatroom?guest_token={token}
```

**连接参数：**
- `guest_token`：游客身份令牌（必填）

**连接流程：**
1. 验证 guest_token 有效性
2. 检查是否被封禁
3. 发送历史消息（最近 50 条）
4. 广播加入通知
5. 更新在线状态到 Redis

**消息格式：**

发送消息（客户端 -> 服务器）：
```json
{
  "type": "message",
  "content": "Hello World!"
}
```

接收消息（服务器 -> 客户端）：
```json
{
  "type": "message",
  "data": {
    "id": 123,
    "sender_nickname": "张三",
    "message_type": "text",
    "content": "Hello World!",
    "created_at": "2026-05-07T15:30:00"
  },
  "timestamp": "2026-05-07T15:30:00"
}
```

**消息类型：**
- `join`：用户加入
- `leave`：用户离开
- `message`：普通消息
- `system`：系统消息
- `announcement`：公告
- `ping`：心跳请求
- `pong`：心跳响应
- `recall`：消息撤回通知
- `ban`：封禁通知
- `kick`：踢出通知
- `error`：错误提示
- `history`：历史消息

### 管理员端点

#### 管理员聊天室 WebSocket
```http
WS /api/v1/chatroom/ws/admin/chatroom?token={admin_token}
```

**连接参数：**
- `token`：管理员访问令牌（必填）

**操作消息格式：**

撤回消息：
```json
{
  "action": "recall",
  "message_id": 123
}
```

封禁用户：
```json
{
  "action": "ban",
  "target_guest_token": "abc123",
  "reason": "违规发言",
  "ban_duration_minutes": 60
}
```

踢出用户：
```json
{
  "action": "kick",
  "target_guest_token": "abc123",
  "reason": "警告一次"
}
```

发送公告：
```json
{
  "action": "announcement",
  "content": "系统将于晚上维护"
}
```

清空历史：
```json
{
  "action": "clear_history"
}
```

#### 管理员操作（HTTP）
```http
POST /api/v1/chatroom/admin/chatroom/action
Authorization: Bearer {admin_token}
```

**请求体：**
```json
{
  "action": "ban",
  "target_guest_token": "abc123",
  "reason": "违规发言",
  "ban_duration_minutes": 60
}
```

**字段说明：**
- `action`：操作类型（recall/ban/kick/announcement/clear_history）
- `target_guest_token`：目标用户令牌（ban/kick 时必填）
- `reason`：操作原因（可选）
- `content`：公告内容（announcement 时必填）
- `ban_duration_minutes`：封禁时长（分钟，ban 时可选，不填为永久）
- `message_id`：消息 ID（recall 时必填）

#### 获取消息管理列表
```http
GET /api/v1/chatroom/admin/chatroom/messages?page=1&page_size=20&include_recalled=false
Authorization: Bearer {admin_token}
```

**查询参数：**
- `page`：页码（默认 1）
- `page_size`：每页数量（1-100，默认 20）
- `include_recalled`：是否包含已撤回消息（默认 false）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "messages": [
      {
        "id": 1,
        "sender_nickname": "张三",
        "message_type": "text",
        "content": "Hello",
        "is_recalled": false,
        "created_at": "2026-05-07T15:30:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

## 数据模型

### ChatMessage（聊天消息）

```python
{
  "id": int,
  "guest_id": int | null,
  "sender_nickname": str,
  "message_type": str,  # text/system/announcement
  "content": str,
  "is_recalled": bool,
  "recalled_at": datetime | null,
  "created_at": datetime
}
```

### ChatBan（封禁记录）

```python
{
  "id": int,
  "guest_id": int,
  "reason": str,
  "banned_by": str,
  "ban_expires_at": datetime | null,
  "is_permanent": bool,
  "created_at": datetime
}
```

## 使用示例

### 前端 WebSocket 集成

#### 1. 建立连接

```javascript
class ChatroomClient {
  constructor(guestToken) {
    this.guestToken = guestToken;
    this.ws = null;
    this.reconnectInterval = 3000;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/api/v1/chatroom/ws/chatroom?guest_token=${this.guestToken}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('聊天室已连接');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error);
    };

    this.ws.onclose = () => {
      console.log('连接已断开，准备重连...');
      setTimeout(() => this.connect(), this.reconnectInterval);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'history':
        this.displayHistory(message.data.messages);
        break;
      case 'message':
        this.displayNewMessage(message.data);
        break;
      case 'join':
        this.showJoinNotification(message.data.nickname);
        break;
      case 'leave':
        this.showLeaveNotification(message.data.guest_token);
        break;
      case 'ping':
        this.sendPong();
        break;
      case 'announcement':
        this.showAnnouncement(message.data.content);
        break;
      case 'recall':
        this.removeMessage(message.data.message_id);
        break;
      case 'ban':
        this.showBanNotification(message.data);
        this.disconnect();
        break;
      case 'kick':
        this.showKickNotification(message.data.reason);
        this.disconnect();
        break;
      case 'error':
        this.showError(message.data.message);
        break;
    }
  }

  sendMessage(content) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket 未连接');
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'message',
      content: content
    }));
  }

  sendPong() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'pong' }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  displayHistory(messages) {
    // 渲染历史消息
  }

  displayNewMessage(message) {
    // 渲染新消息
  }

  showJoinNotification(nickname) {
    // 显示加入提示
  }

  showLeaveNotification(guestToken) {
    // 显示离开提示
  }

  showAnnouncement(content) {
    // 显示公告
  }

  removeMessage(messageId) {
    // 移除被撤回的消息
  }

  showBanNotification(data) {
    // 显示封禁通知
  }

  showKickNotification(reason) {
    // 显示踢出通知
  }

  showError(message) {
    // 显示错误提示
  }
}

// 使用示例
const client = new ChatroomClient('your-guest-token');
client.connect();

// 发送消息
document.getElementById('sendBtn').addEventListener('click', () => {
  const input = document.getElementById('messageInput');
  client.sendMessage(input.value);
  input.value = '';
});
```

#### 2. 管理员控制面板

```javascript
class AdminChatroomClient {
  constructor(adminToken) {
    this.adminToken = adminToken;
    this.ws = null;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/api/v1/chatroom/ws/admin/chatroom?token=${this.adminToken}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('管理员连接已建立');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'success') {
        console.log('操作成功:', message.data.message);
      } else if (message.type === 'error') {
        console.error('操作失败:', message.data.message);
      }
    };
  }

  recallMessage(messageId) {
    this.ws.send(JSON.stringify({
      action: 'recall',
      message_id: messageId
    }));
  }

  banUser(guestToken, reason, durationMinutes) {
    this.ws.send(JSON.stringify({
      action: 'ban',
      target_guest_token: guestToken,
      reason: reason,
      ban_duration_minutes: durationMinutes
    }));
  }

  kickUser(guestToken, reason) {
    this.ws.send(JSON.stringify({
      action: 'kick',
      target_guest_token: guestToken,
      reason: reason
    }));
  }

  sendAnnouncement(content) {
    this.ws.send(JSON.stringify({
      action: 'announcement',
      content: content
    }));
  }

  clearHistory() {
    this.ws.send(JSON.stringify({
      action: 'clear_history'
    }));
  }
}

// 使用示例
const adminClient = new AdminChatroomClient('your-admin-token');
adminClient.connect();

// 封禁用户 60 分钟
adminClient.banUser('guest-token-123', '违规发言', 60);

// 发送公告
adminClient.sendAnnouncement('系统将于 22:00 维护');
```

## Redis 数据结构

### 在线状态
```
Key: chatroom:online:{guest_token}
Type: String
Value: ISO 格式的时间戳
TTL: 65 秒
```

### 限流计数
```
Key: chatroom:rate_limit:{guest_token}
Type: String
Value: 消息计数（1-3）
TTL: 10 秒
```

## 性能优化建议

1. **连接管理**：
   - 使用连接池管理 WebSocket 连接
   - 定期清理僵尸连接
   - 限制单个 IP 的最大连接数

2. **消息广播**：
   - 使用异步广播避免阻塞
   - 对大量在线用户考虑使用 Redis Pub/Sub

3. **历史消息**：
   - 只加载最近 50 条消息
   - 使用分页加载更早的消息
   - 考虑定期归档旧消息

4. **数据库索引**：
   - `chat_messages.created_at`
   - `chat_messages.is_recalled`
   - `chat_bans.guest_id`
   - `chat_bans.ban_expires_at`

## 安全建议

1. **连接认证**：
   - 游客连接必须提供有效 guest_token
   - 管理员连接必须提供有效 admin token
   - 定期刷新和验证 token

2. **消息验证**：
   - 严格验证消息长度（最多 200 字符）
   - 过滤敏感词和恶意内容
   - 防止 XSS 注入

3. **限流保护**：
   - 每个用户 10 秒最多 3 条消息
   - 防止消息轰炸攻击
   - IP 级别的连接限制

4. **封禁机制**：
   - 自动检测恶意行为
   - 支持永久和临时封禁
   - 记录封禁原因和操作人

## 故障排查

### WebSocket 连接失败

1. 检查 guest_token 是否有效
2. 确认用户未被封禁
3. 检查服务器 WebSocket 支持
4. 确认防火墙和代理配置

### 消息发送失败

1. 检查限流状态（10 秒 3 条）
2. 确认消息长度不超过 200 字符
3. 检查是否包含敏感词
4. 确认 WebSocket 连接正常

### 心跳超时

1. 客户端需响应 ping 消息
2. 检查网络稳定性
3. 调整心跳间隔（默认 30 秒）

### 在线状态不准确

1. 检查 Redis 连接
2. 确认 TTL 设置正确（65 秒）
3. 检查心跳机制是否正常

## 依赖项

模块依赖以下组件：

- `FastAPI WebSocket`：实时通信
- `Redis`：在线状态和限流
- `tortoise-orm`：数据持久化
- `GuestIdentity` 模型：游客身份（来自 comments 模块）

## 扩展建议

1. **消息类型**：
   - 支持图片消息
   - 支持表情消息
   - 支持文件分享

2. **聊天功能**：
   - 私聊功能
   - 消息回复/引用
   - 消息反应（点赞/表情）

3. **管理功能**：
   - 禁言（只禁止发言，不断开连接）
   - 慢速模式（限制发言频率）
   - 聊天室关闭/开启

4. **统计分析**：
   - 消息统计
   - 活跃用户分析
   - 违规行为统计

5. **通知系统**：
   - @提及通知
   - 关键词监控
   - 邮件/短信通知
