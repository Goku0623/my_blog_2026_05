from tortoise import fields
from tortoise.models import Model


class ChatMessage(Model):
    TYPE_TEXT = "text"
    TYPE_SYSTEM = "system"
    TYPE_AI = "ai"
    TYPE_ANNOUNCEMENT = "announcement"
    
    TYPE_CHOICES = [
        (TYPE_TEXT, "普通消息"),
        (TYPE_SYSTEM, "系统消息"),
        (TYPE_AI, "AI消息"),
        (TYPE_ANNOUNCEMENT, "公告"),
    ]

    id = fields.IntField(pk=True)
    guest = fields.ForeignKeyField("models.GuestIdentity", related_name="chat_messages", null=True, on_delete=fields.SET_NULL)
    sender_nickname = fields.CharField(max_length=50)
    message_type = fields.CharField(max_length=20, default=TYPE_TEXT)
    content = fields.TextField()
    is_recalled = fields.BooleanField(default=False)
    recalled_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"


class ChatBan(Model):
    id = fields.IntField(pk=True)
    guest = fields.ForeignKeyField("models.GuestIdentity", related_name="chat_bans", on_delete=fields.CASCADE)
    reason = fields.TextField()
    banned_by = fields.CharField(max_length=50)
    ban_expires_at = fields.DatetimeField(null=True)
    is_permanent = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_bans"
