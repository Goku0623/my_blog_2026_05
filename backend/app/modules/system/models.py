from tortoise import fields
from tortoise.models import Model


class AdminNotification(Model):
    TYPE_COMMENT = "new_comment"
    TYPE_GUESTBOOK = "new_guestbook_message"
    TYPE_SYSTEM_ALERT = "system_alert"
    TYPE_N8N_DRAFT = "n8n_draft"

    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=50, index=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField(null=True)
    link = fields.CharField(max_length=500, null=True)
    source_id = fields.IntField(null=True)
    is_read = fields.BooleanField(default=False, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "admin_notifications"


class SiteConfig(Model):
    TYPE_STR = "str"
    TYPE_INT = "int"
    TYPE_BOOL = "bool"
    TYPE_JSON = "json"
    
    TYPE_CHOICES = [
        (TYPE_STR, "字符串"),
        (TYPE_INT, "整数"),
        (TYPE_BOOL, "布尔"),
        (TYPE_JSON, "JSON"),
    ]

    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=100, unique=True, index=True)
    value = fields.TextField()
    value_type = fields.CharField(max_length=20, default=TYPE_STR)
    description = fields.TextField(null=True)
    is_public = fields.BooleanField(default=False)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "site_configs"


class SensitiveWord(Model):
    id = fields.IntField(pk=True)
    word = fields.CharField(max_length=100, unique=True)
    category = fields.CharField(max_length=50, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "sensitive_words"


class OperationLog(Model):
    RESULT_SUCCESS = "success"
    RESULT_FAILURE = "failure"
    
    RESULT_CHOICES = [
        (RESULT_SUCCESS, "成功"),
        (RESULT_FAILURE, "失败"),
    ]

    id = fields.IntField(pk=True)
    operator = fields.CharField(max_length=50)
    action = fields.CharField(max_length=100)
    target_type = fields.CharField(max_length=50, null=True)
    target_id = fields.IntField(null=True)
    detail = fields.TextField(null=True)
    ip_address = fields.CharField(max_length=50)
    result = fields.CharField(max_length=20, default=RESULT_SUCCESS)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "operation_logs"


class ScheduledTask(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    task_path = fields.CharField(max_length=200)
    cron_expression = fields.CharField(max_length=100)
    is_active = fields.BooleanField(default=True)
    last_run_at = fields.DatetimeField(null=True)
    next_run_at = fields.DatetimeField(null=True)
    last_result = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "scheduled_tasks"
