# AI 模块（AI）

## 功能概述

AI 模块提供完整的 AI 能力集成，包括 N8N 自动文章生成、MCP 天气查询、AI 评论回复建议和聊天室 AI 助手功能，支持自动化内容生成和智能交互。

## 核心功能

### 1. N8N 自动文章生成

- **Webhook 接收器**：接收 N8N 工作流推送的文章内容
- **密钥验证**：支持 Header 或 Body 传递验证密钥
- **自动分类**：自动创建或查找文章分类
- **标签管理**：自动创建或关联文章标签
- **Slug 生成**：自动生成唯一的 URL slug
- **草稿状态**：文章创建为草稿，供管理员后续编辑发布

### 2. MCP 天气查询

- **多服务商支持**：支持高德地图、百度地图、OpenWeatherMap
- **多种定位**：支持经纬度、城市名称、IP 自动定位
- **中文描述**：返回中文天气描述
- **智能缓存**：30 分钟主缓存 + 2 小时降级缓存，大幅减少 API 调用
- **城市级缓存**：按城市缓存而非按用户，提高命中率
- **降级策略**：API 失败时返回过期缓存，保证可用性
- **IP 定位**：使用 ip-api.com 获取 IP 地理位置

### 3. AI 评论回复建议

- **管理员工具**：管理员专用功能
- **上下文分析**：支持分析评论上下文
- **OpenAI 兼容**：调用 OpenAI 兼容 API 生成建议
- **Token 统计**：返回模型使用和 token 消耗统计
- **限流保护**：每个管理员每分钟最多 20 次调用

### 4. 聊天室 AI 助手

- **游客可用**：支持游客身份调用
- **对话历史**：维护最近 10 条对话记录
- **实时响应**：快速生成 AI 回复
- **限流保护**：每个游客每小时最多 30 次调用

## API 端点

### 公开端点

#### 获取天气信息
```http
GET /api/v1/ai/weather?latitude=39.9&longitude=116.4&city=北京
```

**查询参数：**
- `latitude`：纬度（可选）
- `longitude`：经度（可选）
- `city`：城市名称（可选）

优先级：坐标 > 城市 > IP 定位

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "city": "北京",
    "temperature": 25.5,
    "feels_like": 24.8,
    "description": "晴朗",
    "humidity": 60,
    "wind_speed": 3.5,
    "icon": "01d",
    "updated_at": "2026-05-07T16:00:00"
  }
}
```

#### AI 聊天助手
```http
POST /api/v1/ai/chat
Headers:
  X-Guest-Token: {guest_token}
  Content-Type: application/json
```

**请求体：**
```json
{
  "message": "你好，请介绍一下这个博客",
  "history": [
    {
      "role": "user",
      "content": "之前的消息"
    },
    {
      "role": "assistant",
      "content": "之前的回复"
    }
  ]
}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "reply": "你好！这是一个基于 FastAPI 构建的现代博客系统...",
    "model_used": "gpt-3.5-turbo"
  }
}
```

**限流**：每个游客每小时最多 30 次调用

### N8N 端点

#### 接收 N8N 文章
```http
POST /api/v1/ai/n8n/article
Headers:
  X-N8N-Secret: {n8n_secret}
  Content-Type: application/json
```

**请求体：**
```json
{
  "title": "文章标题",
  "content": "文章内容（Markdown 格式）",
  "summary": "文章摘要（可选）",
  "category_name": "分类名称（可选）",
  "tags": ["标签1", "标签2"]
}
```

**字段说明：**
- `title`：文章标题（必填）
- `content`：文章内容（必填）
- `summary`：文章摘要（可选）
- `category_name`：分类名称（可选，不存在则自动创建）
- `tags`：标签列表（可选，不存在则自动创建）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "article_id": 123,
    "title": "文章标题",
    "status": "draft",
    "message": "文章已创建为草稿，请登录后台编辑发布"
  }
}
```

### 管理员端点

#### AI 评论回复建议
```http
POST /api/v1/ai/admin/comment-reply
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**请求体：**
```json
{
  "comment_id": 123,
  "article_title": "文章标题",
  "comment_content": "这篇文章写得真好！",
  "context_comments": [
    "之前的评论内容1",
    "之前的评论内容2"
  ]
}
```

**字段说明：**
- `comment_id`：评论 ID（必填）
- `article_title`：文章标题（必填）
- `comment_content`：评论内容（必填）
- `context_comments`：上下文评论列表（可选）

**响应示例：**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "suggested_reply": "感谢您的支持！很高兴文章对您有帮助...",
    "model_used": "gpt-3.5-turbo",
    "tokens_used": 150
  }
}
```

**限流**：每个管理员每分钟最多 20 次调用

## 数据模型

### N8NArticlePayload（N8N 文章负载）

```python
{
  "title": str,
  "content": str,
  "summary": str | null,
  "category_name": str | null,
  "tags": list[str],
  "n8n_secret": str
}
```

### WeatherResponse（天气响应）

```python
{
  "city": str,
  "temperature": float,
  "feels_like": float,
  "description": str,
  "humidity": int,
  "wind_speed": float,
  "icon": str,
  "updated_at": datetime
}
```

### AICommentReplyResponse（AI 评论回复响应）

```python
{
  "suggested_reply": str,
  "model_used": str,
  "tokens_used": int
}
```

### AIChatResponse（AI 聊天响应）

```python
{
  "reply": str,
  "model_used": str
}
```

### ChatMessage（聊天消息）

```python
{
  "role": str,  # user/assistant/system
  "content": str
}
```

## 配置管理

### 环境变量配置

在 `.env` 文件中配置以下变量：

```env
# N8N Integration
N8N_SECRET=your_secure_random_secret_key

# Weather API Configuration
# 支持的服务商：amap (高德), baidu (百度), openweather (OpenWeatherMap)
WEATHER_PROVIDER=amap
WEATHER_API_KEY=your_weather_api_key

# OpenAI Compatible API
AI_API_KEY=your_openai_api_key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

### SiteConfig 表配置

应用启动时会自动从环境变量初始化以下配置到 `SiteConfig` 表：

| Key | Type | Description | Public |
|-----|------|-------------|--------|
| N8N_SECRET | str | N8N 验证密钥 | false |
| WEATHER_PROVIDER | str | 天气服务商 (amap/baidu/openweather) | false |
| WEATHER_API_KEY | str | 天气 API 密钥 | false |
| AI_API_KEY | str | OpenAI 兼容 API 密钥 | false |
| AI_BASE_URL | str | AI API 基础 URL | false |
| AI_MODEL | str | AI 模型名称 | false |

**注意**：如果配置已存在，不会覆盖现有值。

### API 密钥获取

#### 天气 API

各服务商的**免费额度、日调用上限、计费规则会调整**，请以官网文档与控制台为准，本文不写死具体次数。

**高德地图天气 API**
1. 访问 https://lbs.amap.com/
2. 注册开发者账号
3. 创建应用并选择 Web 服务 API
4. 获取 Key（配置到 `WEATHER_API_KEY`）
5. 在控制台查看「配额 / 用量 / 计费」说明
6. 设置 `WEATHER_PROVIDER=amap`

**百度地图天气 API**
1. 访问 https://lbsyun.baidu.com/
2. 注册开发者账号
3. 创建应用
4. 获取 AK（配置到 `WEATHER_API_KEY`）
5. 在控制台查看官方配额说明
6. 设置 `WEATHER_PROVIDER=baidu`

**OpenWeatherMap API**（国际版）
1. 访问 https://openweathermap.org/
2. 注册账号并获取 API key
3. 在订阅与文档中确认当前套餐的限制与计费
4. 设置 `WEATHER_PROVIDER=openweather`

#### OpenAI API
1. 访问 https://platform.openai.com/
2. 注册账号并创建 API key

#### 国内 AI 服务替代方案
- **DeepSeek**: https://platform.deepseek.com/
- **Moonshot AI (Kimi)**: https://platform.moonshot.cn/
- **智谱 AI (GLM)**: https://open.bigmodel.cn/

## Redis 数据结构

### AI 限流计数
```
Key: ai_comment_reply:{admin_username}
Type: String
Value: 调用次数
TTL: 60 秒

Key: ai_chat:{guest_token}
Type: String
Value: 调用次数
TTL: 3600 秒
```

### 天气缓存
```
# 主缓存（30 分钟，减少 API 调用）
Key: weather:v2:{provider}:{city_or_coords}
Type: String
Value: JSON 格式的天气数据
TTL: 1800 秒（30 分钟）

# 降级缓存（2 小时，API 失败时使用）
Key: weather:v2:{provider}:{city_or_coords}:stale
Type: String
Value: JSON 格式的天气数据（可能过期）
TTL: 7200 秒（2 小时）
```

## N8N 工作流配置

### HTTP Request 节点配置

```yaml
方法: POST
URL: https://your-blog-api.com/api/v1/ai/n8n/article
认证: None

Headers:
  - Name: X-N8N-Secret
    Value: {{$env.N8N_SECRET}}
  - Name: Content-Type
    Value: application/json

Body:
  {
    "title": "{{$json.title}}",
    "content": "{{$json.content}}",
    "summary": "{{$json.summary}}",
    "category_name": "AI生成",
    "tags": ["自动生成", "AI"]
  }
```

### 工作流示例

一个完整的自动文章生成工作流：

1. **Schedule Trigger**：每天定时触发
2. **HTTP Request**：获取新闻源或内容
3. **Function**：处理和格式化数据
4. **HTTP Request**：调用 OpenAI 生成文章
5. **HTTP Request**：发送到博客后台（本模块）

## 性能优化与成本控制

### 天气 API 成本优化（重点）

1. **智能缓存策略**：
   - **主缓存 30 分钟**：正常情况下，同一城市的请求在 30 分钟内命中缓存
   - **降级缓存 2 小时**：API 失败或超额时，返回 2 小时内的历史数据
   - **城市级缓存**：按城市名缓存，而非按用户 IP，大幅提高命中率

2. **服务商选择**：
   - 对比各平台**当前**公布的配额与单价后自选（高德 / 百度 / OpenWeather 等）
   - 低配额时更依赖下面的缓存与合并请求策略

3. **调用量估算思路（示例，非承诺）**：
   - 无缓存时，请求量近似「独立用户数 × 人均请求次数」
   - 有城市级缓存、TTL 为 T 分钟时，单日上游调用量近似「不同城市（或缓存键）数 × (1440 / T)」，实际还会受冷门城市首次命中等影响
   - 将估算结果与**你在控制台看到的配额**对比，必要时加长 TTL、缩小展示场景或换服务商

4. **降级保障**：
   - API 调用失败时，自动返回 2 小时内的缓存数据
   - 保证用户体验，不会因为 API 问题导致功能不可用

### 通用性能优化

1. **异步操作**：
   - 所有 I/O 操作使用 async/await
   - httpx AsyncClient 异步 HTTP 请求
   - Redis 异步客户端

2. **超时控制**：
   - IP 定位 API：5 秒超时
   - 天气 API：10 秒超时
   - AI API：30 秒超时

3. **限流实现**：
   - Redis 计数器
   - 自动过期
   - 可配置限制和时间窗口

## 安全建议

1. **密钥管理**：
   - N8N 密钥验证（Header 或 Body）
   - 所有 API 密钥标记为非公开
   - 不在日志中记录敏感信息

2. **认证授权**：
   - N8N 端点需要密钥验证
   - 管理员端点需要 Admin Token
   - 游客端点需要 Guest Token

3. **限流保护**：
   - AI 评论回复：20 次/分钟/管理员
   - AI 聊天：30 次/小时/游客
   - 防止 API 滥用和费用暴增

4. **输入验证**：
   - Pydantic 模型验证
   - 类型检查
   - 必填项验证

5. **错误处理**：
   - 统一异常处理
   - 友好错误消息
   - 不泄露系统信息

## 天气服务商切换指南

### 切换到高德地图

1. 注册高德开放平台账号：https://lbs.amap.com/
2. 创建应用，选择 "Web 服务 API"
3. 获取 Key
4. 修改配置：
   ```env
   WEATHER_PROVIDER=amap
   WEATHER_API_KEY=你的高德key
   ```
5. 重启应用

### 切换到百度地图

1. 注册百度地图开放平台：https://lbsyun.baidu.com/
2. 创建应用
3. 获取 AK
4. 修改配置：
   ```env
   WEATHER_PROVIDER=baidu
   WEATHER_API_KEY=你的百度AK
   ```
5. 重启应用

### 切换到 OpenWeatherMap

1. 注册 OpenWeatherMap：https://openweathermap.org/
2. 获取 API Key
3. 修改配置：
   ```env
   WEATHER_PROVIDER=openweather
   WEATHER_API_KEY=你的OpenWeather key
   ```
4. 重启应用

### 运行时切换

也可以直接修改数据库 `site_configs` 表：

```sql
UPDATE site_configs SET value = 'amap' WHERE key = 'WEATHER_PROVIDER';
UPDATE site_configs SET value = '你的key' WHERE key = 'WEATHER_API_KEY';
```

无需重启，立即生效（下次请求时使用新配置）。

## 故障排查

### N8N 文章创建失败

1. 检查 N8N_SECRET 是否正确
2. 确认 Header 或 Body 中包含密钥
3. 验证 JSON 格式是否正确
4. 查看服务器日志

### 天气查询失败

1. 验证 WEATHER_API_KEY 是否有效
2. 检查 API key 是否已激活
3. 确认未超过调用限额
4. 检查网络连接

### AI 调用失败

1. 验证 AI_API_KEY 是否正确
2. 检查 AI_BASE_URL 是否可访问
3. 确认模型名称是否正确
4. 检查 API 配额和余额

### 限流触发

1. 检查 Redis 连接是否正常
2. 等待限流时间窗口过期
3. 查看 Redis 中的限流 key
4. 根据需要调整限流参数

## 依赖项

模块依赖以下组件：

- `FastAPI`：Web 框架
- `httpx`：异步 HTTP 客户端
- `Redis`：缓存和限流
- `tortoise-orm`：数据库 ORM
- `pydantic`：数据验证

外部 API：
- OpenWeatherMap API（天气数据）
- OpenAI API（或兼容服务）

## 扩展建议

1. **AI 功能增强**：
   - 支持流式响应（SSE）
   - 添加对话历史持久化
   - 实现本地模型部署选项
   - 支持更多 AI 模型

2. **天气服务优化**：
   - 支持多个天气 API 提供商
   - 实现降级策略
   - 添加天气预报功能
   - 支持更多气象数据

3. **N8N 集成扩展**：
   - 支持文章更新
   - 添加 Webhook 回调
   - 批量文章导入
   - 定时发布功能

4. **监控和统计**：
   - API 调用统计
   - 费用追踪
   - 性能监控
   - 错误率统计

5. **高级功能**：
   - AI 内容审核
   - 智能标签推荐
   - 文章摘要生成
   - SEO 优化建议
