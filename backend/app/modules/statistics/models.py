from tortoise import fields
from tortoise.models import Model


class DailyStats(Model):
    id = fields.IntField(pk=True)
    stat_date = fields.DateField(unique=True)
    new_articles = fields.IntField(default=0)
    total_views = fields.IntField(default=0)
    new_comments = fields.IntField(default=0)
    unique_visitors = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "daily_stats"


class APICallLog(Model):
    id = fields.IntField(pk=True)
    endpoint = fields.CharField(max_length=200)
    method = fields.CharField(max_length=10)
    status_code = fields.IntField()
    response_time_ms = fields.IntField()
    ip_address = fields.CharField(max_length=50)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "api_call_logs"
