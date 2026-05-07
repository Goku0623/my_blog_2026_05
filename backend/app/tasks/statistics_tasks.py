import asyncio
from tortoise import Tortoise

from app.tasks.celery_app import celery_app
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


async def _record_daily_snapshot_async():
    from app.modules.statistics.service import StatisticsService
    
    await StatisticsService.record_daily_snapshot()
    
    return {"success": True}


@celery_app.task(name="statistics.record_daily_snapshot")
def record_daily_snapshot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_record_daily_snapshot_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
