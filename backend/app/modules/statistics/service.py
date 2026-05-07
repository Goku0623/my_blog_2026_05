import asyncio
import shutil
from datetime import datetime, date, timedelta
from typing import Optional
from tortoise.functions import Sum, Count
from tortoise.expressions import Q

from app.modules.articles.models import Article
from app.modules.comments.models import Comment
from app.modules.statistics.models import DailyStats, APICallLog
from app.modules.statistics.schemas import (
    DashboardData, TrendResponse, TrendData,
    APIMonitorResponse, APIMetrics, RecentError,
    CeleryTaskStats, SystemHealthResponse, HealthStatus,
    TopArticle, RecentCommentActivity
)
from app.core.redis_client import get_redis_client
from app.modules.chatroom.ws_manager import manager as ws_manager


class StatisticsService:
    
    @staticmethod
    async def get_dashboard_data() -> DashboardData:
        redis = await get_redis_client()
        cache_key = "statistics:dashboard"
        
        cached_data = await redis.get(cache_key)
        if cached_data:
            import json
            return DashboardData(**json.loads(cached_data))
        
        today = date.today()
        
        total_articles = await Article.all().count()
        published_articles = await Article.filter(status=Article.STATUS_PUBLISHED).count()
        draft_articles = await Article.filter(status=Article.STATUS_DRAFT).count()
        
        total_views_result = await Article.all().annotate(
            total=Sum("view_count")
        ).values("total")
        total_views = total_views_result[0]["total"] if total_views_result and total_views_result[0]["total"] else 0
        
        total_comments = await Comment.all().count()
        pending_comments = await Comment.filter(status=Comment.STATUS_PENDING).count()
        
        online_users = await ws_manager.get_online_count()
        
        daily_stat = await DailyStats.get_or_none(stat_date=today)
        if daily_stat:
            today_views = daily_stat.total_views
            today_comments = daily_stat.new_comments
            today_new_articles = daily_stat.new_articles
        else:
            today_start = datetime.combine(today, datetime.min.time())
            today_views = 0
            today_comments = await Comment.filter(created_at__gte=today_start).count()
            today_new_articles = await Article.filter(created_at__gte=today_start).count()
        
        data = DashboardData(
            total_articles=total_articles,
            published_articles=published_articles,
            draft_articles=draft_articles,
            total_views=total_views,
            total_comments=total_comments,
            pending_comments=pending_comments,
            online_users=online_users,
            today_views=today_views,
            today_comments=today_comments,
            today_new_articles=today_new_articles
        )
        
        import json
        await redis.setex(cache_key, 60, json.dumps(data.model_dump()))
        
        return data
    
    @staticmethod
    async def get_trend_data(metric: str, period: str) -> TrendResponse:
        if period == "day":
            days = 30
            date_list = [date.today() - timedelta(days=i) for i in range(days-1, -1, -1)]
        elif period == "week":
            weeks = 12
            date_list = [date.today() - timedelta(weeks=i) for i in range(weeks-1, -1, -1)]
        elif period == "month":
            months = 12
            date_list = []
            current_date = date.today()
            for i in range(months-1, -1, -1):
                month_date = date(current_date.year, current_date.month, 1) - timedelta(days=i*30)
                date_list.append(month_date)
        else:
            date_list = [date.today() - timedelta(days=i) for i in range(29, -1, -1)]
        
        trend_data = []
        
        for d in date_list:
            if period == "day":
                stat = await DailyStats.get_or_none(stat_date=d)
                if stat:
                    if metric == "views":
                        value = stat.total_views
                    elif metric == "comments":
                        value = stat.new_comments
                    elif metric == "articles":
                        value = stat.new_articles
                    elif metric == "visitors":
                        value = stat.unique_visitors
                    else:
                        value = 0
                else:
                    value = 0
                
                trend_data.append(TrendData(date=d.isoformat(), value=value))
            elif period == "week":
                week_start = d - timedelta(days=d.weekday())
                week_end = week_start + timedelta(days=6)
                
                stats = await DailyStats.filter(
                    stat_date__gte=week_start,
                    stat_date__lte=week_end
                ).all()
                
                if metric == "views":
                    value = sum(s.total_views for s in stats)
                elif metric == "comments":
                    value = sum(s.new_comments for s in stats)
                elif metric == "articles":
                    value = sum(s.new_articles for s in stats)
                elif metric == "visitors":
                    value = sum(s.unique_visitors for s in stats)
                else:
                    value = 0
                
                trend_data.append(TrendData(date=week_start.isoformat(), value=value))
            elif period == "month":
                month_stats = await DailyStats.filter(
                    stat_date__year=d.year,
                    stat_date__month=d.month
                ).all()
                
                if metric == "views":
                    value = sum(s.total_views for s in month_stats)
                elif metric == "comments":
                    value = sum(s.new_comments for s in month_stats)
                elif metric == "articles":
                    value = sum(s.new_articles for s in month_stats)
                elif metric == "visitors":
                    value = sum(s.unique_visitors for s in month_stats)
                else:
                    value = 0
                
                trend_data.append(TrendData(date=f"{d.year}-{d.month:02d}", value=value))
        
        return TrendResponse(
            period=period,
            metric=metric,
            data=trend_data
        )
    
    @staticmethod
    async def get_api_metrics(hours: int = 24) -> APIMonitorResponse:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        logs = await APICallLog.filter(created_at__gte=time_threshold).all()
        
        total_calls = len(logs)
        
        if total_calls == 0:
            return APIMonitorResponse(
                total_calls=0,
                avg_response_ms=0.0,
                error_rate=0.0,
                top_endpoints=[],
                recent_errors=[]
            )
        
        total_response_time = sum(log.response_time_ms for log in logs)
        avg_response_ms = total_response_time / total_calls
        
        error_logs = [log for log in logs if log.status_code >= 400]
        error_rate = len(error_logs) / total_calls
        
        endpoint_stats = {}
        for log in logs:
            key = f"{log.method}:{log.endpoint}"
            if key not in endpoint_stats:
                endpoint_stats[key] = {
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "calls": [],
                    "errors": 0
                }
            endpoint_stats[key]["calls"].append(log.response_time_ms)
            if log.status_code >= 400:
                endpoint_stats[key]["errors"] += 1
        
        top_endpoints = []
        for key, stats in endpoint_stats.items():
            call_count = len(stats["calls"])
            avg_resp = sum(stats["calls"]) / call_count
            success_count = call_count - stats["errors"]
            success_rate = success_count / call_count
            
            top_endpoints.append(APIMetrics(
                endpoint=stats["endpoint"],
                method=stats["method"],
                call_count=call_count,
                avg_response_ms=round(avg_resp, 2),
                success_rate=round(success_rate, 2),
                error_count=stats["errors"]
            ))
        
        top_endpoints.sort(key=lambda x: x.call_count, reverse=True)
        top_endpoints = top_endpoints[:10]
        
        recent_errors = [
            RecentError(
                endpoint=log.endpoint,
                method=log.method,
                status_code=log.status_code,
                error_message=log.error_message,
                ip_address=log.ip_address,
                created_at=log.created_at
            )
            for log in sorted(error_logs, key=lambda x: x.created_at, reverse=True)[:10]
        ]
        
        return APIMonitorResponse(
            total_calls=total_calls,
            avg_response_ms=round(avg_response_ms, 2),
            error_rate=round(error_rate, 2),
            top_endpoints=top_endpoints,
            recent_errors=recent_errors
        )
    
    @staticmethod
    async def get_celery_stats() -> list[CeleryTaskStats]:
        try:
            from app.core.celery_app import celery_app
            
            inspect = celery_app.control.inspect()
            
            stats_dict = inspect.stats()
            if not stats_dict:
                return []
            
            active_tasks = inspect.active()
            registered_tasks = inspect.registered()
            
            task_stats = []
            
            if registered_tasks:
                for worker, tasks in registered_tasks.items():
                    for task_name in tasks:
                        task_stats.append(CeleryTaskStats(
                            task_name=task_name,
                            total=0,
                            succeeded=0,
                            failed=0,
                            pending=0,
                            avg_runtime_ms=0.0
                        ))
            
            return task_stats
        except Exception:
            return []
    
    @staticmethod
    async def check_system_health() -> SystemHealthResponse:
        services = []
        
        async def check_postgres():
            try:
                start = datetime.utcnow()
                await Article.all().count()
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                
                return HealthStatus(
                    service="PostgreSQL",
                    status="healthy",
                    latency_ms=round(latency, 2),
                    detail=None
                )
            except Exception as e:
                return HealthStatus(
                    service="PostgreSQL",
                    status="unhealthy",
                    latency_ms=None,
                    detail=str(e)
                )
        
        async def check_redis():
            try:
                redis = await get_redis_client()
                start = datetime.utcnow()
                await redis.ping()
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                
                return HealthStatus(
                    service="Redis",
                    status="healthy",
                    latency_ms=round(latency, 2),
                    detail=None
                )
            except Exception as e:
                return HealthStatus(
                    service="Redis",
                    status="unhealthy",
                    latency_ms=None,
                    detail=str(e)
                )
        
        async def check_celery():
            try:
                from app.core.celery_app import celery_app
                
                start = datetime.utcnow()
                inspect = celery_app.control.inspect()
                stats = inspect.stats()
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                
                if stats:
                    return HealthStatus(
                        service="Celery Worker",
                        status="healthy",
                        latency_ms=round(latency, 2),
                        detail=f"{len(stats)} workers active"
                    )
                else:
                    return HealthStatus(
                        service="Celery Worker",
                        status="degraded",
                        latency_ms=None,
                        detail="No workers found"
                    )
            except Exception as e:
                return HealthStatus(
                    service="Celery Worker",
                    status="unhealthy",
                    latency_ms=None,
                    detail=str(e)
                )
        
        async def check_disk():
            try:
                start = datetime.utcnow()
                disk_usage = shutil.disk_usage("/")
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                
                free_gb = disk_usage.free / (1024 ** 3)
                total_gb = disk_usage.total / (1024 ** 3)
                usage_percent = (disk_usage.used / disk_usage.total) * 100
                
                if usage_percent > 90:
                    status = "unhealthy"
                elif usage_percent > 80:
                    status = "degraded"
                else:
                    status = "healthy"
                
                return HealthStatus(
                    service="Disk Space",
                    status=status,
                    latency_ms=round(latency, 2),
                    detail=f"{free_gb:.2f}GB free of {total_gb:.2f}GB ({usage_percent:.1f}% used)"
                )
            except Exception as e:
                return HealthStatus(
                    service="Disk Space",
                    status="unhealthy",
                    latency_ms=None,
                    detail=str(e)
                )
        
        try:
            results = await asyncio.gather(
                check_postgres(),
                check_redis(),
                check_celery(),
                check_disk(),
                return_exceptions=True
            )
            
            for result in results:
                if isinstance(result, Exception):
                    services.append(HealthStatus(
                        service="Unknown",
                        status="unhealthy",
                        latency_ms=None,
                        detail=str(result)
                    ))
                else:
                    services.append(result)
        except Exception as e:
            services.append(HealthStatus(
                service="System",
                status="unhealthy",
                latency_ms=None,
                detail=str(e)
            ))
        
        unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
        degraded_count = sum(1 for s in services if s.status == "degraded")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return SystemHealthResponse(
            overall_status=overall_status,
            services=services,
            checked_at=datetime.utcnow()
        )
    
    @staticmethod
    async def record_daily_snapshot():
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        new_articles = await Article.filter(created_at__gte=today_start).count()
        
        new_comments = await Comment.filter(created_at__gte=today_start).count()
        
        from app.modules.articles.models import ArticleView
        unique_visitors = await ArticleView.filter(
            viewed_at__gte=today_start
        ).distinct().count()
        
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
    
    @staticmethod
    async def send_alert_notification(subject: str, message: str):
        from app.core.celery_app import celery_app
        
        try:
            celery_app.send_task(
                "app.tasks.send_email",
                args=[subject, message]
            )
        except Exception:
            pass
    
    @staticmethod
    async def get_top_viewed_articles(limit: int = 10) -> list[TopArticle]:
        articles = await Article.filter(
            status=Article.STATUS_PUBLISHED
        ).order_by("-view_count").limit(limit).all()
        
        return [
            TopArticle(
                id=article.id,
                title=article.title,
                slug=article.slug,
                view_count=article.view_count,
                published_at=article.published_at
            )
            for article in articles
        ]
    
    @staticmethod
    async def get_recent_comment_activity(limit: int = 10) -> list[RecentCommentActivity]:
        from tortoise.functions import Max
        
        comments = await Comment.filter(
            status__in=[Comment.STATUS_PENDING, Comment.STATUS_APPROVED]
        ).group_by("article_id").annotate(
            comment_count=Count("id"),
            latest_comment_at=Max("created_at")
        ).order_by("-latest_comment_at").limit(limit).all()
        
        activities = []
        for comment in comments:
            article = await comment.article
            if article:
                article_comments = await Comment.filter(article_id=article.id).count()
                latest = await Comment.filter(article_id=article.id).order_by("-created_at").first()
                
                activities.append(RecentCommentActivity(
                    article_id=article.id,
                    article_title=article.title,
                    comment_count=article_comments,
                    latest_comment_at=latest.created_at if latest else datetime.utcnow()
                ))
        
        return activities
