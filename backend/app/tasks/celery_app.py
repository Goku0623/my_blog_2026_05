from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "blog_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.backup_tasks",
        "app.tasks.cache_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.statistics_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule={
        "daily-snapshot": {
            "task": "statistics.record_daily_snapshot",
            "schedule": crontab(hour=0, minute=5),
        },
        "clear-expired-blacklist": {
            "task": "cache.clear_expired_token_blacklist",
            "schedule": crontab(minute=0),
        },
        "clear-old-api-logs": {
            "task": "cache.clear_old_api_logs",
            "schedule": crontab(hour=3, minute=0),
        },
        "database-backup": {
            "task": "backup.database",
            "schedule": crontab(hour=2, minute=0),
        },
        "clear-expired-views": {
            "task": "cache.clear_expired_article_views",
            "schedule": crontab(hour=1, minute=0),
        },
    },
)
