# AI 模块

## 核心功能

- N8N Webhook 接收文章（密钥验证，自动创建分类/标签/Slug，推入草稿）
- 天气查询（高德/百度/OpenWeatherMap，IP 定位，30 分钟缓存 + 2 小时降级缓存）
- AI 评论回复建议（管理员专用，OpenAI 兼容 API，限流 20 次/分钟）

## API 端点

| 端点 | 方法 | 认证 | 说明 |
|---|---|---|---|
| `/ai/weather` | GET | 否 | 天气查询 |
| `/ai/n8n/article` | POST | X-N8N-Secret | N8N 推送文章草稿 |
| `/ai/admin/comment-reply` | POST | Bearer | AI 评论回复建议 |

## N8N 文章推送

`POST /api/v1/ai/n8n/article`，Header: `X-N8N-Secret`。

```json
{
  "title": "标题",
  "content": "Markdown 内容",
  "summary": "摘要（可选）",
  "category_name": "分类（可选，自动创建）",
  "tags": ["标签1", "标签2"]
}
```

N8N 推送草稿后会自动发送邮件通知管理员。

## 配置项

| Key | 说明 |
|---|---|
| `N8N_SECRET` | N8N Webhook 验证密钥 |
| `WEATHER_PROVIDER` | 天气服务商（amap/baidu/openweather） |
| `WEATHER_API_KEY` | 天气 API 密钥 |
| `AI_API_KEY` | OpenAI 兼容 API 密钥 |
| `AI_BASE_URL` | API 基础 URL |
| `AI_MODEL` | 模型名称 |
