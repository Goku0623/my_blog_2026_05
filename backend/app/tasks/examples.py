"""
Celery 任务使用示例

演示如何在代码中调用各种 Celery 任务
"""

from app.tasks.backup_tasks import backup_database
from app.tasks.cache_tasks import (
    clear_expired_token_blacklist,
    clear_old_api_logs,
    clear_expired_article_views,
    refresh_sensitive_words_cache,
)
from app.tasks.ai_tasks import process_n8n_article
from app.tasks.statistics_tasks import record_daily_snapshot


def example_backup():
    """执行数据库备份"""
    result = backup_database.delay()
    print(f"备份任务已提交: {result.id}")
    return result


def example_cache_cleanup():
    """执行缓存清理"""
    tasks = [
        clear_expired_token_blacklist.delay(),
        clear_old_api_logs.delay(),
        clear_expired_article_views.delay(),
    ]
    print(f"已提交 {len(tasks)} 个清理任务")
    return tasks


def example_process_article(article_id: int):
    """处理 N8N 推送的文章"""
    result = process_n8n_article.delay(article_id)
    print(f"文章处理任务已提交: {result.id}")
    return result


def example_manual_snapshot():
    """手动触发统计快照"""
    result = record_daily_snapshot.delay()
    print(f"统计快照任务已提交: {result.id}")
    return result


def example_get_task_result(task_id: str):
    """获取任务执行结果"""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    if result.ready():
        if result.successful():
            print(f"任务完成: {result.result}")
        else:
            print(f"任务失败: {result.traceback}")
    else:
        print(f"任务状态: {result.state}")
    
    return result


def example_schedule_task():
    """定时执行任务（使用 ETA）"""
    from datetime import datetime, timedelta
    
    eta = datetime.now() + timedelta(minutes=10)
    
    result = backup_database.apply_async(eta=eta)
    print(f"任务将在 {eta} 执行: {result.id}")
    return result


def example_retry_task():
    """重试失败的任务"""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app
    
    task_id = "your-task-id-here"
    result = AsyncResult(task_id, app=celery_app)
    
    if result.failed():
        new_result = backup_database.retry()
        print(f"任务已重试: {new_result.id}")
        return new_result


def example_chain_tasks():
    """链式执行任务"""
    from celery import chain
    
    workflow = chain(
        clear_old_api_logs.s(),
        clear_expired_article_views.s(),
        record_daily_snapshot.s(),
    )
    
    result = workflow.apply_async()
    print(f"工作流已提交: {result.id}")
    return result


def example_group_tasks():
    """并行执行多个任务"""
    from celery import group
    
    job = group([
        clear_expired_token_blacklist.s(),
        clear_old_api_logs.s(),
        clear_expired_article_views.s(),
    ])
    
    result = job.apply_async()
    print(f"任务组已提交，共 {len(result)} 个任务")
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Celery 任务使用示例")
    print("=" * 60)
    
    print("\n1. 执行数据库备份")
    example_backup()
    
    print("\n2. 执行缓存清理")
    example_cache_cleanup()
    
    print("\n3. 手动触发统计快照")
    example_manual_snapshot()
    
    print("\n5. 并行执行多个清理任务")
    example_group_tasks()
    
    print("\n" + "=" * 60)
    print("所有示例任务已提交！")
    print("使用 Flower 监控面板查看执行情况: http://localhost:5555")
    print("=" * 60)
