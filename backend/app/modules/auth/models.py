from tortoise import fields
from tortoise.models import Model


class AdminUser(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, index=True)
    email = fields.CharField(max_length=100, unique=True, null=True, index=True)
    hashed_password = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    last_login_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "admin_users"


class TokenBlacklist(Model):
    id = fields.IntField(pk=True)
    jti = fields.CharField(max_length=255, unique=True, index=True)
    token_type = fields.CharField(max_length=20)
    expired_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "token_blacklist"


class LoginAttempt(Model):
    id = fields.IntField(pk=True)
    ip_address = fields.CharField(max_length=50)
    username_tried = fields.CharField(max_length=50)
    success = fields.BooleanField(default=False)
    attempted_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "login_attempts"
