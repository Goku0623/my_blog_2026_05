from tortoise import fields
from tortoise.models import Model


class GuestIdentity(Model):
    id = fields.IntField(pk=True)
    guest_token = fields.CharField(max_length=255, unique=True, index=True)
    nickname = fields.CharField(max_length=50, unique=True, null=True)
    ip_address = fields.CharField(max_length=50)
    user_agent = fields.CharField(max_length=255, null=True)
    is_banned = fields.BooleanField(default=False)
    ban_reason = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guest_identities"


class Comment(Model):
    STATUS_APPROVED = "approved"
    STATUS_HIDDEN = "hidden"
    STATUS_DELETED = "deleted"
    
    STATUS_CHOICES = [
        (STATUS_APPROVED, "已发布"),
        (STATUS_HIDDEN, "已隐藏"),
        (STATUS_DELETED, "已删除"),
    ]

    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField("models.Article", related_name="comments", on_delete=fields.CASCADE)
    guest = fields.ForeignKeyField("models.GuestIdentity", related_name="comments", on_delete=fields.CASCADE)
    parent = fields.ForeignKeyField("models.Comment", related_name="replies", null=True, on_delete=fields.CASCADE)
    reply_to_nickname = fields.CharField(max_length=50, null=True)
    content = fields.TextField()
    rendered_content = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default=STATUS_APPROVED)
    is_pinned = fields.BooleanField(default=False)
    admin_reply = fields.TextField(null=True)
    ip_address = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "comments"
