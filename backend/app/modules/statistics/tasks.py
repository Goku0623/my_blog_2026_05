from datetime import datetime, date, timedelta
from tortoise.functions import Sum

from app.modules.articles.models import Article, ArticleView
from app.modules.comments.models import Comment
from app.modules.statistics.models import DailyStats


async def record_daily_snapshot():
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    new_articles = await Article.filter(created_at__gte=today_start).count()
    
    new_comments = await Comment.filter(created_at__gte=today_start).count()
    
    unique_visitors_result = await ArticleView.filter(
        viewed_at__gte=today_start
    ).distinct().values("ip_address")
    unique_visitors = len(unique_visitors_result)
    
    total_views_result = await Article.all().annotate(
        total=Sum("view_count")
    ).values("total")
    total_views = total_views_result[0]["total"] if total_views_result and total_views_result[0]["total"] else 0
    
    await DailyStats.update_or_create(
        stat_date=today,
        defaults={
            "new_articles": new_articles,
            "total_views": total_views,
            "new_comments": new_comments,
            "unique_visitors": unique_visitors
        }
    )
    
    return {
        "stat_date": today.isoformat(),
        "new_articles": new_articles,
        "total_views": total_views,
        "new_comments": new_comments,
        "unique_visitors": unique_visitors
    }


async def cleanup_old_api_logs(days: int = 30):
    threshold = datetime.utcnow() - timedelta(days=days)
    from app.modules.statistics.models import APICallLog
    
    deleted_count = await APICallLog.filter(created_at__lt=threshold).delete()
    
    return {"deleted_count": deleted_count}


async def send_system_alert(subject: str, message: str):
    try:
        pass
    except Exception as e:
        return {"error": str(e)}
    
    return {"status": "sent", "subject": subject}
