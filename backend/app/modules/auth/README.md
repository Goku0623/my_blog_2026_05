# 认证模块

## 功能

- JWT 双令牌（access 30 分钟 + refresh 7 天），Token 黑名单（Redis + DB 双写）
- 登录限流（同 IP 每分钟 10 次，15 分钟失败 5 次锁定）
- 密码修改、个人资料更新（自动同步到评论身份和 ADMIN_EMAIL 配置）
- 登录日志记录

## API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/auth/login` | POST | 登录 |
| `/auth/refresh` | POST | 刷新令牌 |
| `/auth/me` | GET | 当前用户信息 |
| `/auth/change-password` | PUT | 修改密码 |
| `/auth/logout` | POST | 登出 |
| `/auth/profile` | PUT | 更新个人资料（用户名/邮箱/头像） |

## 配置项

```env
SECRET_KEY=xxx
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 创建管理员

```bash
uv run python create_admin.py
# admin / admin123456
```
