import asyncio
from datetime import datetime, timedelta
from tortoise import Tortoise

from app.tasks.celery_app import celery_app
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


async def _clear_expired_token_blacklist_async():
    from app.core.redis_client import get_redis_client
    
    redis = await get_redis_client()
    pattern = "token_blacklist:*"
    
    cursor = 0
    deleted_count = 0
    
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        for key in keys:
            ttl = await redis.ttl(key)
            if ttl == -2:
                deleted_count += 1
        
        if cursor == 0:
            break
    
    return {"deleted": deleted_count}


@celery_app.task(name="cache.clear_expired_token_blacklist")
def clear_expired_token_blacklist():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_clear_expired_token_blacklist_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()


async def _clear_old_api_logs_async():
    from app.modules.statistics.models import APICallLog
    
    days_ago = datetime.now() - timedelta(days=7)
    deleted = await APICallLog.filter(created_at__lt=days_ago).delete()
    
    return {"deleted": deleted}


@celery_app.task(name="cache.clear_old_api_logs")
def clear_old_api_logs():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_clear_old_api_logs_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()


async def _clear_expired_article_views_async():
    from app.modules.articles.models import ArticleView
    
    days_ago = datetime.now() - timedelta(days=30)
    deleted = await ArticleView.filter(viewed_at__lt=days_ago).delete()
    
    return {"deleted": deleted}


@celery_app.task(name="cache.clear_expired_article_views")
def clear_expired_article_views():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_clear_expired_article_views_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()


async def _refresh_sensitive_words_cache_async():
    from app.modules.system.service import SensitiveWordService
    
    await SensitiveWordService.refresh_sensitive_words_cache()
    return {"success": True}


@celery_app.task(name="cache.refresh_sensitive_words")
def refresh_sensitive_words_cache():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_refresh_sensitive_words_cache_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()


async def _clear_old_operation_logs_async():
    from app.modules.system.models import OperationLog

    days_ago = datetime.now() - timedelta(days=30)
    deleted = await OperationLog.filter(created_at__lt=days_ago).delete()

    return {"deleted": deleted}


@celery_app.task(name="cache.clear_old_operation_logs")
def clear_old_operation_logs():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_clear_old_operation_logs_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
