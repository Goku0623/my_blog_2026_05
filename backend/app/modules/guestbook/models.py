from tortoise import fields
from tortoise.models import Model


class GuestbookMessage(Model):
    STATUS_APPROVED = "approved"
    STATUS_HIDDEN = "hidden"
    STATUS_DELETED = "deleted"

    STATUS_CHOICES = [
        (STATUS_APPROVED, "已发布"),
        (STATUS_HIDDEN, "已隐藏"),
        (STATUS_DELETED, "已删除"),
    ]

    id = fields.IntField(pk=True)
    guest = fields.ForeignKeyField("models.GuestIdentity", related_name="guestbook_messages", on_delete=fields.CASCADE)
    content = fields.TextField()
    rendered_content = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default=STATUS_APPROVED)
    ip_address = fields.CharField(max_length=50)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guestbook_messages"