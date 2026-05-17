import asyncio
from tortoise import Tortoise

from app.tasks.celery_app import celery_app
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


async def _publish_due_scheduled_articles_async():
    from app.modules.articles.service import ArticleService

    published_count = await ArticleService.publish_due_scheduled_articles()
    backfilled_count = await ArticleService.backfill_missing_published_at()
    return {
        "published_count": published_count,
        "backfilled_count": backfilled_count,
    }


@celery_app.task(name="articles.publish_due_scheduled")
def publish_due_scheduled():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_publish_due_scheduled_articles_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
