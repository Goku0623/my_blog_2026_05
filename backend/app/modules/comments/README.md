# 评论模块

## 核心功能

- 游客匿名评论（自动分配 guest_token），支持设置昵称和封禁
- 楼中楼回复（一层嵌套），支持 Markdown 内容
- 敏感词过滤（Redis 缓存 + 数据库），日限额 + 短时限流保护
- 管理员审核（置顶/通过/隐藏/删除）、回复、WebSocket 实时通知
- 新评论/回复管理员 → 管理员站内通知（管理员发言不通知）
- AI 自动回复（后台异步，不阻塞请求）

## API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/articles/{id}/comments` | GET | 文章评论列表（分页） |
| `/comments` | POST | 提交评论 |
| `/guest/identity` | GET | 获取/创建游客身份 |
| `/guest/nickname` | PUT | 设置游客昵称 |
| `/admin/comments` | GET | 管理员评论列表（多条件筛选） |
| `/admin/comments/{id}/action` | POST | 管理操作（pin/approve/hide/delete） |
| `/admin/comments/{id}/reply` | POST | 管理员回复 |
| `/ws/admin/comments` | WS | WebSocket 实时通知 |

## 限流规则

- 短时限流：游客每分钟 5 条
- 日限额：每用户每日 2 条、每文章每用户每日 2 条（可配置）
- 指纹并行限流（防无痕窗口绕过）
- 管理员不受任何限流
