import asyncio
import shutil
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from tortoise.functions import Sum

from app.modules.articles.models import Article, ArticleView
from app.modules.comments.models import Comment
from app.modules.statistics.models import DailyStats, APICallLog
from app.modules.statistics.schemas import (
    DashboardData, TrendResponse, TrendData,
    APIMonitorResponse, APIMetrics, RecentError,
    CeleryTaskStats, SystemHealthResponse, HealthStatus,
    TopArticle, RecentCommentActivity, CategoryDistribution
)
from app.core.redis_client import get_redis_client


class StatisticsService:

    @staticmethod
    async def _count_metric_in_range(start_dt: datetime, end_dt: datetime, metric: str) -> int:
        if metric == "articles":
            return await Article.filter(created_at__gte=start_dt, created_at__lt=end_dt).count()
        if metric == "comments":
            return await Comment.filter(
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                status=Comment.STATUS_APPROVED,
            ).count()
        if metric == "visitors":
            return await ArticleView.filter(
                viewed_at__gte=start_dt,
                viewed_at__lt=end_dt,
            ).distinct().count()
        if metric == "views":
            return await ArticleView.filter(viewed_at__gte=start_dt, viewed_at__lt=end_dt).count()
        return 0

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        seconds = max(0, seconds)
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, sec = divmod(rem, 60)
        return f"{days}d {hours:02d}:{minutes:02d}:{sec:02d}"

    @staticmethod
    def _resolve_metric_value(stats: list[DailyStats], metric: str) -> int:
        if metric == "views":
            return sum(s.total_views for s in stats)
        if metric == "comments":
            return sum(s.new_comments for s in stats)
        if metric == "articles":
            return sum(s.new_articles for s in stats)
        if metric == "visitors":
            return sum(s.unique_visitors for s in stats)
        return 0
    
    @staticmethod
    async def get_dashboard_data() -> DashboardData:
        cache_key = "statistics:dashboard"
        redis = None
        try:
            redis = await get_redis_client()
            cached_data = await redis.get(cache_key)
            if cached_data:
                import json
                return DashboardData(**json.loads(cached_data))
        except Exception:
            redis = None
        
        today = date.today()
        
        (
            total_articles,
            published_articles,
            draft_articles,
            total_views,
            total_comments,
        ) = await asyncio.gather(
            Article.all().count(),
            Article.filter(status=Article.STATUS_PUBLISHED).count(),
            Article.filter(status=Article.STATUS_DRAFT).count(),
            ArticleView.all().count(),
            Comment.all().count(),
        )
        
        daily_stat = await DailyStats.get_or_none(stat_date=today)
        if daily_stat:
            today_views = daily_stat.total_views
            today_comments = daily_stat.new_comments
            today_new_articles = daily_stat.new_articles
        else:
            today_start = datetime.combine(today, datetime.min.time())
            today_views = 0
            today_comments, today_new_articles = await asyncio.gather(
                Comment.filter(created_at__gte=today_start).count(),
                Article.filter(created_at__gte=today_start).count(),
            )
        
        data = DashboardData(
            total_articles=total_articles,
            published_articles=published_articles,
            draft_articles=draft_articles,
            total_views=total_views,
            total_comments=total_comments,
            today_views=today_views,
            today_comments=today_comments,
            today_new_articles=today_new_articles
        )
        
        if redis:
            try:
                import json
                await redis.setex(cache_key, 60, json.dumps(data.model_dump()))
            except Exception:
                pass
        
        return data
    
    @staticmethod
    async def get_trend_data(metric: str, period: str) -> TrendResponse:
        if period not in {"day", "week", "month"}:
            period = "day"
        if metric not in {"views", "comments", "articles", "visitors"}:
            metric = "views"

        today = date.today()
        trend_data: list[TrendData] = []

        if period == "day":
            date_list = [today - timedelta(days=i) for i in range(29, -1, -1)]

            for day in date_list:
                start_dt = datetime.combine(day, datetime.min.time())
                end_dt = start_dt + timedelta(days=1)
                value = await StatisticsService._count_metric_in_range(start_dt, end_dt, metric)
                trend_data.append(TrendData(date=day.isoformat(), value=value))
        elif period == "week":
            current_week_start = today - timedelta(days=today.weekday())
            week_starts = [
                current_week_start - timedelta(weeks=i) for i in range(11, -1, -1)
            ]

            for week_start in week_starts:
                start_dt = datetime.combine(week_start, datetime.min.time())
                end_dt = start_dt + timedelta(days=7)
                value = await StatisticsService._count_metric_in_range(start_dt, end_dt, metric)
                trend_data.append(TrendData(date=week_start.isoformat(), value=value))
        else:
            month_starts: list[date] = []
            cursor = date(today.year, today.month, 1)
            for _ in range(12):
                month_starts.append(cursor)
                cursor = date(cursor.year - 1, 12, 1) if cursor.month == 1 else date(cursor.year, cursor.month - 1, 1)
            month_starts.reverse()

            for month_start in month_starts:
                month_end = (
                    date(month_start.year + 1, 1, 1)
                    if month_start.month == 12
                    else date(month_start.year, month_start.month + 1, 1)
                )
                start_dt = datetime.combine(month_start, datetime.min.time())
                end_dt = datetime.combine(month_end, datetime.min.time())
                value = await StatisticsService._count_metric_in_range(start_dt, end_dt, metric)
                trend_data.append(
                    TrendData(date=f"{month_start.year}-{month_start.month:02d}", value=value)
                )

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
    async def _get_site_started_at() -> Optional[datetime]:
        from app.modules.system.models import SiteConfig
        cfg = await SiteConfig.get_or_none(key="SITE_STARTED_AT")
        if not cfg or not cfg.value:
            return None
        try:
            return datetime.fromisoformat(cfg.value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    async def check_system_health() -> SystemHealthResponse:
        cache_key = "statistics:system_health"
        redis = None
        try:
            redis = await get_redis_client()
            cached_data = await redis.get(cache_key)
            if cached_data:
                import json
                return SystemHealthResponse(**json.loads(cached_data))
        except Exception:
            redis = None

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

        started_at = await StatisticsService._get_site_started_at()
        if started_at:
            uptime_seconds = int((datetime.now(timezone.utc) - started_at).total_seconds())
            uptime = StatisticsService._format_uptime(uptime_seconds)
        else:
            uptime = "-"

        health = SystemHealthResponse(
            overall_status=overall_status,
            services=services,
            checked_at=datetime.now(timezone.utc),
            uptime=uptime,
            started_at=started_at,
        )
        if redis:
            try:
                import json
                await redis.setex(cache_key, 30, json.dumps(health.model_dump(mode="json")))
            except Exception:
                pass
        return health
    
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
        from app.modules.system.service import AdminNotificationService
        from app.modules.system.models import AdminNotification
        from app.tasks.notification_tasks import send_alert_email

        await AdminNotificationService.create_notification(
            type=AdminNotification.TYPE_SYSTEM_ALERT,
            title=subject,
            content=message,
        )
        await send_alert_email(subject, f"<html><body><p>{message}</p></body></html>")
    
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
        comments = await Comment.filter(
            status=Comment.STATUS_APPROVED
        ).order_by("-created_at").limit(limit).prefetch_related("article", "guest")
        from app.modules.comments.service import resolve_guest_display_name, resolve_guest_avatar

        activities = []
        for comment in comments:
            article = await comment.article
            guest = await comment.guest
            if not article:
                continue

            article_comments = await Comment.filter(
                article_id=article.id, status=Comment.STATUS_APPROVED
            ).count()
            guest_name = await resolve_guest_display_name(guest) if guest else "游客"
            guest_avatar = await resolve_guest_avatar(guest) if guest else None

            activities.append(RecentCommentActivity(
                id=comment.id,
                article_id=article.id,
                article_title=article.title,
                guest_name=guest_name,
                guest_avatar=guest_avatar,
                content=comment.content,
                created_at=comment.created_at,
                comment_count=article_comments,
                latest_comment_at=comment.created_at,
            ))

        return activities

    @staticmethod
    async def get_category_distribution() -> list[CategoryDistribution]:
        from app.modules.articles.models import Category

        categories = await Category.all().order_by("sort_order", "name")
        result: list[CategoryDistribution] = []
        for category in categories:
            article_count = await Article.filter(
                category_id=category.id,
                status=Article.STATUS_PUBLISHED
            ).count()
            result.append(
                CategoryDistribution(
                    category_name=category.name,
                    article_count=article_count,
                )
            )
        return result
