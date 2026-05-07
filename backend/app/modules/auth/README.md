# 认证模块 (Auth Module)

完整的 JWT 认证系统，包含登录、token 刷新、登出、密码修改等功能。

## 功能特性

### 🔐 安全特性
- **JWT 双令牌机制**: access_token (30分钟) + refresh_token (7天)
- **Token 黑名单**: Redis + PostgreSQL 双重存储，防止令牌重放攻击
- **密码加密**: bcrypt 算法，自动加盐
- **登录限流**: 
  - 同一 IP 每分钟最多 10 次登录请求
  - 15 分钟内失败 5 次将被临时锁定
- **登录日志**: 记录所有登录尝试（成功/失败、IP、时间）

### 📊 数据模型

#### AdminUser (管理员)
```python
- id: 主键
- username: 用户名（唯一）
- email: 邮箱（可选，唯一）
- hashed_password: 加密后的密码
- is_active: 是否激活
- last_login_at: 最后登录时间
- created_at: 创建时间
- updated_at: 更新时间
```

#### TokenBlacklist (令牌黑名单)
```python
- id: 主键
- jti: JWT ID（唯一）
- token_type: access/refresh
- expired_at: 过期时间
- created_at: 创建时间
```

#### LoginAttempt (登录日志)
```python
- id: 主键
- ip_address: IP 地址
- username_tried: 尝试登录的用户名
- success: 是否成功
- attempted_at: 尝试时间
```

## API 端点

### 1. POST /api/v1/auth/login
管理员登录

**请求体:**
```json
{
  "username": "admin",
  "password": "admin123456"
}
```

**成功响应 (200):**
```json
{
  "code": 0,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**错误响应:**
- `401`: 用户名或密码错误
- `403`: 账号未激活
- `429`: 登录次数过多

**限流:** 每分钟 10 次

---

### 2. POST /api/v1/auth/refresh
刷新访问令牌

**请求体:**
```json
{
  "refresh_token": "eyJ..."
}
```

**成功响应 (200):**
```json
{
  "code": 0,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**错误响应:**
- `401`: refresh_token 无效或已过期

**注意:** 旧的 refresh_token 会被加入黑名单

---

### 3. GET /api/v1/auth/me
获取当前用户信息

**请求头:**
```
Authorization: Bearer <access_token>
```

**成功响应 (200):**
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "last_login_at": "2026-05-07T15:30:00",
    "created_at": "2026-05-07T10:00:00"
  }
}
```

**错误响应:**
- `401`: Token 无效或已过期
- `403`: 账号未激活

---

### 4. PUT /api/v1/auth/change-password
修改密码

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "old_password": "admin123456",
  "new_password": "newSecurePassword123"
}
```

**成功响应 (200):**
```json
{
  "code": 0,
  "message": "Password changed successfully",
  "data": null
}
```

**错误响应:**
- `400`: 旧密码错误，或新密码与旧密码相同
- `401`: Token 无效

---

### 5. POST /api/v1/auth/logout
登出

**请求头:**
```
Authorization: Bearer <access_token>
```

**成功响应 (200):**
```json
{
  "code": 0,
  "message": "Logout successful",
  "data": null
}
```

**说明:** access_token 和 refresh_token 都会被加入黑名单

---

## Service 层方法

### AuthService.authenticate_admin()
验证管理员账号密码

```python
admin = await AuthService.authenticate_admin(
    username="admin",
    password="admin123456",
    ip_address="127.0.0.1"
)
```

**功能:**
- 验证用户名和密码
- 检查账号是否激活
- 记录登录日志（成功/失败）
- 更新最后登录时间
- 登录失败限流保护（15分钟5次失败锁定）

---

### AuthService.create_token_pair()
生成令牌对

```python
tokens = await AuthService.create_token_pair(admin)
# {
#   "access_token": "...",
#   "refresh_token": "...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }
```

---

### AuthService.refresh_access_token()
刷新访问令牌

```python
tokens = await AuthService.refresh_access_token(refresh_token)
```

**功能:**
- 验证 refresh_token 有效性
- 检查是否在黑名单中
- 生成新的 access_token
- 将旧的 refresh_token 加入黑名单

---

### AuthService.logout()
登出（令牌失效）

```python
await AuthService.logout(
    access_jti="uuid-xxx",
    refresh_jti="uuid-yyy",
    access_ttl=1800,
    refresh_ttl=604800
)
```

**功能:**
- 将两个 token 的 JTI 加入 Redis 黑名单
- 在数据库中记录黑名单（持久化）

---

### AuthService.change_password()
修改密码

```python
await AuthService.change_password(
    admin=current_admin,
    old_password="old123",
    new_password="new456"
)
```

---

### AuthService.create_first_admin()
创建首个管理员（命令行工具）

```python
admin = await AuthService.create_first_admin()
# 返回创建的管理员，如果已存在则返回 None
```

---

## 使用示例

### 1. 创建首个管理员

```bash
cd backend
uv run python create_admin.py
```

### 2. 登录获取令牌

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

### 3. 使用令牌访问受保护接口

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJ..."
```

### 4. 刷新令牌

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ..."
  }'
```

### 5. 修改密码

```bash
curl -X PUT http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123456",
    "new_password": "newSecurePassword123"
  }'
```

### 6. 登出

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJ..."
```

---

## 测试

运行自动化测试：

```bash
cd backend
uv run python test_auth.py
```

测试包含：
1. 登录流程
2. 获取用户信息
3. 刷新令牌
4. 登出
5. 登出后访问（验证令牌失效）

---

## 安全建议

1. **生产环境必须修改默认密码**
2. **SECRET_KEY 使用强随机字符串**: `openssl rand -hex 32`
3. **启用 HTTPS**: 防止令牌被窃听
4. **定期清理过期黑名单记录**: 
   ```python
   await TokenBlacklist.filter(
       expired_at__lt=datetime.now()
   ).delete()
   ```
5. **监控登录失败日志**: 检测暴力破解攻击
6. **配置合适的令牌过期时间**: 根据业务需求调整

---

## 配置项

在 `backend/.env` 中配置：

```env
# JWT 配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis 配置（用于令牌黑名单）
REDIS_URL=redis://localhost:6379/0
```

---

## 依赖关系

- `python-jose[cryptography]`: JWT 生成和验证
- `passlib[bcrypt]`: 密码加密
- `bcrypt`: bcrypt 算法
- `redis`: Token 黑名单存储
- `slowapi`: API 限流

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误（如密码格式不正确） |
| 401 | 未授权（Token 无效或已过期） |
| 403 | 禁止访问（账号未激活） |
| 422 | 验证错误（字段格式不正确） |
| 429 | 请求过多（触发限流） |
| 500 | 服务器内部错误 |
