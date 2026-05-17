from app.tasks.celery_app import celery_app
from app.tasks import backup_tasks
from app.tasks import cache_tasks
from app.tasks import ai_tasks
from app.tasks import statistics_tasks
from app.tasks import articles_tasks


__all__ = [
    "celery_app",
    "backup_tasks",
    "cache_tasks",
    "ai_tasks",
    "statistics_tasks",
    "articles_tasks",
]
