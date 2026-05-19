import json
from typing import Optional, List, Dict, Set
from datetime import datetime
from tortoise.exceptions import IntegrityError

from app.modules.system.models import SiteConfig, SensitiveWord, OperationLog, ScheduledTask
from app.modules.auth.models import AdminUser
from app.core.redis_client import get_redis_client
from app.common.exceptions import NotFoundException, BadRequestException


class SiteConfigService:
    CONFIG_CACHE_TTL = 300
    PUBLIC_CONFIG_CACHE_KEY = "config:public:bundle"
    PUBLIC_CONFIG_CACHE_TTL = 180
    DEFAULT_ARTICLE_COVER_IMAGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE"
    DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_THUMB"
    DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY = "DEFAULT_ARTICLE_COVER_IMAGE_LARGE"
    
    DEFAULT_CONFIGS = {
        "SITE_NAME": ("我的博客", "str", "站点名称", True),
        "SITE_DESCRIPTION": ("基于 FastAPI + Vue3 的现代化博客系统", "str", "站点描述", True),
        "SITE_KEYWORDS": ("博客,技术,分享,Vue,FastAPI", "str", "站点关键词", True),
        "SITE_AUTHOR": ("博主", "str", "站点作者", True),
        "ICP_NUMBER": ("", "str", "ICP备案号", True),
        "COMMENT_ENABLED": ("true", "bool", "评论功能开关", True),
        "AI_ENABLED": ("true", "bool", "AI功能开关", True),
        "COMMENT_NEED_REVIEW": ("true", "bool", "评论需要审核", True),
        "COMMENT_RATE_LIMIT": ("5", "int", "评论速率限制（每分钟）", False),
        "COMMENT_DAILY_LIMIT_PER_USER": ("2", "int", "评论：每用户每日上限（次）", False),
        "COMMENT_DAILY_LIMIT_PER_ARTICLE_PER_USER": ("2", "int", "评论：每用户每篇文章每日上限（次）", False),
        "GUESTBOOK_DAILY_LIMIT_PER_USER": ("2", "int", "留言墙：每用户每日上限（次）", False),
        "COVER_IMAGE_MAX_SIZE_MB": ("2", "int", "封面图最大体积（MB）", True),
        DEFAULT_ARTICLE_COVER_IMAGE_KEY: ("", "str", "默认文章封面图（支持 data URL 或 http(s) URL）", False),
        DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY: ("", "str", "默认文章封面缩略图（16:9）", False),
        DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY: ("", "str", "默认文章封面大图（16:9）", False),
        "AI_API_KEY": ("", "str", "AI API密钥", False),
        "AI_BASE_URL": ("", "str", "AI API地址", False),
        "AI_MODEL": ("", "str", "AI模型名称", False),
        "WEATHER_API_KEY": ("", "str", "天气API密钥", False),
        "WEATHER_PROVIDER": ("amap", "str", "天气服务商 (amap/baidu/openweather)", False),
        "WEATHER_API_BASE_URL": ("", "str", "天气 API 地址（可选，覆盖默认地址）", False),
        "WEATHER_CITY_NAME": ("深圳市", "str", "天气展示城市名称（前端展示用）", True),
        "WEATHER_CITY_CODE": ("440300", "str", "天气城市编码（如高德 adcode）", True),
        "N8N_ASSISTANT_WEBHOOK_URL": ("", "str", "AI 助手 N8N Webhook 地址", False),
        "ASSISTANT_GUEST_DAILY_LIMIT": ("3", "int", "AI 助手游客每日提问上限（0 表示不限额）", False),
        "N8N_SECRET": ("", "str", "N8N Webhook密钥", False),
        "ADMIN_EMAIL": ("", "str", "管理员邮箱", True),
        "SMTP_HOST": ("", "str", "SMTP服务器地址", False),
        "SMTP_PORT": ("587", "int", "SMTP端口", False),
        "SMTP_USER": ("", "str", "SMTP用户名", False),
        "SMTP_PASSWORD": ("", "str", "SMTP密码", False),
        "SMTP_FROM": ("", "str", "发件人地址", False),
        "BACKUP_DIR": ("./backups", "str", "备份目录", False),
        "N8N_BLOG_INGEST_WEBHOOK_URL": ("", "str", "博客文章入库 N8N Webhook 地址", False),
        "SITE_URL": ("", "str", "站点完整 URL（例如 https://example.com）", False),
        "GITHUB_URL": ("", "str", "GitHub 主页地址", True),
        "BILIBILI_URL": ("", "str", "Bilibili 主页地址", True),
        "ABOUT_ME_CONTENT": ("", "str", "关于我页面正文内容（支持换行，以\\n分隔）", True),
    }

    @staticmethod
    async def get_all_configs(is_public_only: bool = False) -> List[SiteConfig]:
        query = SiteConfig.all()
        if is_public_only:
            query = query.filter(is_public=True)
        return await query

    @staticmethod
    async def get_config(key: str) -> Optional[str]:
        redis = await get_redis_client()
        cache_key = f"config:{key}"
        
        cached_value = await redis.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        config = await SiteConfig.get_or_none(key=key)
        if config:
            await redis.setex(cache_key, SiteConfigService.CONFIG_CACHE_TTL, config.value)
            return config.value
        
        return None

    @staticmethod
    async def get_configs_map(keys: List[str]) -> Dict[str, Optional[str]]:
        unique_keys: List[str] = []
        seen = set()
        for key in keys:
            if key and key not in seen:
                unique_keys.append(key)
                seen.add(key)

        if not unique_keys:
            return {}

        result: Dict[str, Optional[str]] = {}
        missing_keys: List[str] = list(unique_keys)
        redis = None

        try:
            redis = await get_redis_client()
            if redis is not None and hasattr(redis, "mget"):
                cache_keys = [f"config:{key}" for key in unique_keys]
                cached_values = await redis.mget(cache_keys)
                missing_keys = []
                for key, cached_value in zip(unique_keys, cached_values):
                    if cached_value is None:
                        missing_keys.append(key)
                    else:
                        result[key] = cached_value
        except Exception:
            redis = None
            missing_keys = list(unique_keys)

        if not missing_keys:
            return result

        configs = await SiteConfig.filter(key__in=missing_keys)
        db_map = {config.key: config.value for config in configs}

        has_cache_updates = False
        pipeline = None
        if redis is not None and hasattr(redis, "pipeline"):
            try:
                pipeline = redis.pipeline()
            except Exception:
                pipeline = None

        for key in missing_keys:
            value = db_map.get(key)
            result[key] = value
            if value is not None:
                if pipeline is not None:
                    pipeline.setex(f"config:{key}", SiteConfigService.CONFIG_CACHE_TTL, value)
                    has_cache_updates = True
                elif redis is not None and hasattr(redis, "setex"):
                    try:
                        await redis.setex(f"config:{key}", SiteConfigService.CONFIG_CACHE_TTL, value)
                    except Exception:
                        pass

        if has_cache_updates and pipeline is not None:
            try:
                await pipeline.execute()
            except Exception:
                pass

        return result

    @staticmethod
    async def update_config(key: str, value: str, admin: AdminUser):
        if key == SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_KEY:
            config, old_value, normalized_value = await SiteConfigService._update_default_article_cover_config(value)
            await OperationLogService.log_operation(
                operator=admin.username,
                action="update_config",
                target_type="site_config",
                target_id=config.id,
                detail=f"更新配置 {key}: {old_value} -> {normalized_value}",
                ip="system",
                result="success"
            )
            return config

        config = await SiteConfig.get_or_none(key=key)
        if not config:
            raise NotFoundException(f"配置项 {key} 不存在")
        
        old_value = config.value
        config.value = value
        await config.save()
        
        redis = await get_redis_client()
        await redis.delete(f"config:{key}")
        await redis.delete(SiteConfigService.PUBLIC_CONFIG_CACHE_KEY)
        
        await OperationLogService.log_operation(
            operator=admin.username,
            action="update_config",
            target_type="site_config",
            target_id=config.id,
            detail=f"更新配置 {key}: {old_value} -> {value}",
            ip="system",
            result="success"
        )
        
        return config

    @staticmethod
    async def bulk_update_configs(configs: List[Dict[str, str]], admin: AdminUser):
        updated = []
        redis = await get_redis_client()
        for item in configs:
            key = item.get("key")
            value = item.get("value")
            if key and value is not None:
                if key == SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_KEY:
                    config, _, _ = await SiteConfigService._update_default_article_cover_config(value)
                    updated.append(config)
                    continue

                config = await SiteConfig.get_or_none(key=key)
                if config:
                    config.value = value
                    await config.save()
                    
                    await redis.delete(f"config:{key}")
                    updated.append(config)
        await redis.delete(SiteConfigService.PUBLIC_CONFIG_CACHE_KEY)
        
        await OperationLogService.log_operation(
            operator=admin.username,
            action="bulk_update_config",
            target_type="site_config",
            target_id=None,
            detail=f"批量更新 {len(updated)} 个配置项",
            ip="system",
            result="success"
        )
        
        return updated

    @staticmethod
    async def _update_default_article_cover_config(value: Optional[str]) -> tuple[SiteConfig, str, str]:
        """更新默认文章封面，并同步产出缩略图与大图变体。"""
        config = await SiteConfig.get_or_none(key=SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_KEY)
        if not config:
            raise NotFoundException(f"配置项 {SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_KEY} 不存在")

        old_value = config.value
        normalized_cover = ""
        cover_thumb = ""
        cover_large = ""

        normalized_input = (value or "").strip()
        if normalized_input:
            from app.modules.articles.service import ArticleService

            normalized_cover = await ArticleService._normalize_cover_image(normalized_input) or ""
            if normalized_cover:
                cover_thumb, cover_large = await ArticleService._generate_cover_variants(normalized_cover)
                cover_thumb = cover_thumb or ""
                cover_large = cover_large or ""

        config.value = normalized_cover
        await config.save()

        thumb_config = await SiteConfig.get_or_none(key=SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY)
        if thumb_config:
            thumb_config.value = cover_thumb
            await thumb_config.save()

        large_config = await SiteConfig.get_or_none(key=SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY)
        if large_config:
            large_config.value = cover_large
            await large_config.save()

        redis = await get_redis_client()
        await redis.delete(f"config:{SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_KEY}")
        await redis.delete(f"config:{SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_THUMB_KEY}")
        await redis.delete(f"config:{SiteConfigService.DEFAULT_ARTICLE_COVER_IMAGE_LARGE_KEY}")
        await redis.delete(SiteConfigService.PUBLIC_CONFIG_CACHE_KEY)

        return config, old_value, normalized_cover

    @staticmethod
    async def get_public_configs() -> Dict[str, object]:
        """返回前端友好结构（snake_case 键名 + 类型转换）

        前端 SiteConfig 只关心一组固定字段，这里同时返回 raw 原始键值，
        方便管理端复用。
        """
        redis = None
        try:
            redis = await get_redis_client()
            cached = await redis.get(SiteConfigService.PUBLIC_CONFIG_CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception:
            redis = None

        configs = await SiteConfig.filter(is_public=True)
        raw: Dict[str, str] = {c.key: c.value for c in configs}

        def _bool(key: str, default: bool = True) -> bool:
            v = raw.get(key)
            if v is None:
                return default
            return str(v).strip().lower() in {"1", "true", "yes", "on"}

        def _str(key: str, default: str = "") -> str:
            v = raw.get(key)
            return v if v not in (None, "") else default

        def _int(key: str, default: int) -> int:
            v = raw.get(key)
            try:
                return int(v) if v is not None else default
            except (TypeError, ValueError):
                return default

        admin_avatar = ""
        try:
            admin = await AdminUser.filter(is_active=True).order_by("id").first()
            if admin and admin.avatar:
                admin_avatar = admin.avatar
        except Exception:
            pass

        payload = {
            "site_name": _str("SITE_NAME", "我的博客"),
            "site_description": _str("SITE_DESCRIPTION", "一个现代化的博客系统"),
            "site_keywords": _str("SITE_KEYWORDS", "博客,技术,分享"),
            "site_author": _str("SITE_AUTHOR", "博主"),
            "icp_number": _str("ICP_NUMBER", ""),
            "admin_email": _str("ADMIN_EMAIL", ""),
            "admin_avatar": admin_avatar,
            "comment_enabled": _bool("COMMENT_ENABLED", True),
            "comment_audit_enabled": _bool("COMMENT_NEED_REVIEW", True),
            "ai_enabled": _bool("AI_ENABLED", True),
            "cover_image_max_size_mb": max(1, min(20, _int("COVER_IMAGE_MAX_SIZE_MB", 2))),
            "weather_city_name": _str("WEATHER_CITY_NAME", "深圳市"),
            "weather_city_code": _str("WEATHER_CITY_CODE", "440300"),
            "github_url": _str("GITHUB_URL", ""),
            "bilibili_url": _str("BILIBILI_URL", ""),
            "site_started_at": _str("SITE_STARTED_AT", ""),
            "about_me_content": _str("ABOUT_ME_CONTENT", ""),
        }
        if redis:
            try:
                await redis.setex(
                    SiteConfigService.PUBLIC_CONFIG_CACHE_KEY,
                    SiteConfigService.PUBLIC_CONFIG_CACHE_TTL,
                    json.dumps(payload, ensure_ascii=False),
                )
            except Exception:
                pass
        return payload

    @staticmethod
    async def init_default_configs():
        existing = {c.key: c for c in await SiteConfig.all()}

        for key, (value, value_type, description, is_public) in SiteConfigService.DEFAULT_CONFIGS.items():
            if key not in existing:
                await SiteConfig.create(
                    key=key,
                    value=value,
                    value_type=value_type,
                    description=description,
                    is_public=is_public,
                )
            else:
                cfg = existing[key]
                changed = False
                if cfg.is_public != is_public:
                    cfg.is_public = is_public
                    changed = True
                if cfg.value_type != value_type:
                    cfg.value_type = value_type
                    changed = True
                if (cfg.description or "") != description:
                    cfg.description = description
                    changed = True
                if changed:
                    await cfg.save()


class FeatureSwitchService:
    @staticmethod
    async def _get_bool_config(key: str, default: bool = True) -> bool:
        redis = await get_redis_client()
        cache_key = f"config:{key}"
        
        cached_value = await redis.get(cache_key)
        if cached_value is not None:
            return cached_value.lower() == "true"
        
        config = await SiteConfig.get_or_none(key=key)
        if config:
            value = config.value.lower() == "true"
            await redis.setex(cache_key, 300, config.value)
            return value
        
        return default

    @staticmethod
    async def is_comment_enabled() -> bool:
        return await FeatureSwitchService._get_bool_config("COMMENT_ENABLED", True)

    @staticmethod
    async def is_ai_enabled() -> bool:
        return await FeatureSwitchService._get_bool_config("AI_ENABLED", True)


class SensitiveWordService:
    CACHE_KEY = "sensitive_words"
    CACHE_TTL = 600

    @staticmethod
    async def create_sensitive_word(word: str, category: Optional[str] = None) -> SensitiveWord:
        existing = await SensitiveWord.get_or_none(word=word)
        if existing:
            raise BadRequestException(f"敏感词 '{word}' 已存在")
        
        sensitive_word = await SensitiveWord.create(word=word, category=category)
        await SensitiveWordService.refresh_sensitive_words_cache()
        return sensitive_word

    @staticmethod
    async def bulk_import_sensitive_words(items: List[Dict[str, Optional[str]]]) -> Dict[str, int]:
        created = 0
        skipped = 0

        normalized_items: List[Dict[str, Optional[str]]] = []
        seen_words: Set[str] = set()
        for item in items:
            word = (item.get("word") or "").strip()
            category = (item.get("category") or "").strip() or None
            if not word:
                skipped += 1
                continue

            dedupe_key = word.lower()
            if dedupe_key in seen_words:
                skipped += 1
                continue
            seen_words.add(dedupe_key)
            normalized_items.append({"word": word, "category": category})

        if not normalized_items:
            return {"created": 0, "skipped": skipped}

        existing_words = await SensitiveWord.filter(
            word__in=[item["word"] for item in normalized_items]
        ).values_list("word", flat=True)
        existing_set = {word.lower() for word in existing_words}

        for item in normalized_items:
            word = item["word"] or ""
            category = item.get("category")
            if word.lower() in existing_set:
                skipped += 1
                continue

            try:
                await SensitiveWord.create(word=word, category=category)
                created += 1
                existing_set.add(word.lower())
            except IntegrityError:
                skipped += 1

        if created > 0:
            await SensitiveWordService.refresh_sensitive_words_cache()

        return {"created": created, "skipped": skipped}

    @staticmethod
    async def delete_sensitive_word(word_id: int):
        word = await SensitiveWord.get_or_none(id=word_id)
        if not word:
            raise NotFoundException("敏感词不存在")
        
        await word.delete()
        await SensitiveWordService.refresh_sensitive_words_cache()

    @staticmethod
    async def list_sensitive_words(category: Optional[str] = None, is_active: Optional[bool] = None) -> List[SensitiveWord]:
        query = SensitiveWord.all()
        if category:
            query = query.filter(category=category)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        return await query

    @staticmethod
    async def get_sensitive_words_cached() -> Set[str]:
        redis = await get_redis_client()
        cached = await redis.get(SensitiveWordService.CACHE_KEY)
        
        if cached:
            return set(json.loads(cached))
        
        words = await SensitiveWord.filter(is_active=True).values_list("word", flat=True)
        word_set = set(words)
        
        await redis.setex(
            SensitiveWordService.CACHE_KEY,
            SensitiveWordService.CACHE_TTL,
            json.dumps(list(word_set))
        )
        
        return word_set

    @staticmethod
    async def refresh_sensitive_words_cache():
        redis = await get_redis_client()
        words = await SensitiveWord.filter(is_active=True).values_list("word", flat=True)
        word_set = set(words)
        
        await redis.setex(
            SensitiveWordService.CACHE_KEY,
            SensitiveWordService.CACHE_TTL,
            json.dumps(list(word_set))
        )


class OperationLogService:
    @staticmethod
    async def log_operation(
        operator: str,
        action: str,
        target_type: Optional[str],
        target_id: Optional[int],
        detail: Optional[str],
        ip: str,
        result: str = "success"
    ):
        await OperationLog.create(
            operator=operator,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip,
            result=result
        )

    @staticmethod
    async def query_logs(
        operator: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[OperationLog], int]:
        query = OperationLog.all()
        
        if operator:
            query = query.filter(operator__icontains=operator)
        if action:
            query = query.filter(action__icontains=action)
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)
        
        total = await query.count()
        
        offset = (page - 1) * page_size
        logs = await query.order_by("-created_at").offset(offset).limit(page_size)
        
        return logs, total


class ScheduledTaskService:
    @staticmethod
    async def list_tasks() -> List[ScheduledTask]:
        return await ScheduledTask.all()

    @staticmethod
    async def update_task(
        task_id: int,
        is_active: Optional[bool] = None,
        cron_expression: Optional[str] = None
    ) -> ScheduledTask:
        task = await ScheduledTask.get_or_none(id=task_id)
        if not task:
            raise NotFoundException("定时任务不存在")
        
        if is_active is not None:
            task.is_active = is_active
        if cron_expression is not None:
            task.cron_expression = cron_expression
        
        await task.save()
        return task

    @staticmethod
    async def trigger_task_manually(task_name: str):
        task = await ScheduledTask.get_or_none(name=task_name)
        if not task:
            raise NotFoundException("定时任务不存在")

        return {"message": f"任务 {task_name} 已触发执行"}


class AdminNotificationService:
    UNREAD_COUNT_CACHE_KEY = "system:notifications:unread_count"
    UNREAD_COUNT_CACHE_TTL = 15

    @staticmethod
    async def create_notification(
        type: str,
        title: str,
        content: Optional[str] = None,
        link: Optional[str] = None,
        source_id: Optional[int] = None,
    ):
        from app.modules.system.models import AdminNotification
        await AdminNotification.create(
            type=type,
            title=title,
            content=content,
            link=link,
            source_id=source_id,
        )
        try:
            redis = await get_redis_client()
            await redis.delete(AdminNotificationService.UNREAD_COUNT_CACHE_KEY)
        except Exception:
            pass

    @staticmethod
    async def get_unread_count() -> int:
        from app.modules.system.models import AdminNotification
        redis = None
        try:
            redis = await get_redis_client()
            cached = await redis.get(AdminNotificationService.UNREAD_COUNT_CACHE_KEY)
            if cached is not None:
                return int(cached)
        except Exception:
            redis = None

        count = await AdminNotification.filter(is_read=False).count()
        if redis:
            try:
                await redis.setex(
                    AdminNotificationService.UNREAD_COUNT_CACHE_KEY,
                    AdminNotificationService.UNREAD_COUNT_CACHE_TTL,
                    str(count),
                )
            except Exception:
                pass
        return count

    @staticmethod
    async def list_notifications(page: int = 1, page_size: int = 20):
        from app.modules.system.models import AdminNotification
        query = AdminNotification.all().order_by("-created_at")
        total = await query.count()
        offset = (page - 1) * page_size
        items = await query.offset(offset).limit(page_size)
        return list(items), total

    @staticmethod
    async def mark_as_read(notification_id: int):
        from app.modules.system.models import AdminNotification
        notification = await AdminNotification.get_or_none(id=notification_id)
        if notification:
            notification.is_read = True
            await notification.save()
            try:
                redis = await get_redis_client()
                await redis.delete(AdminNotificationService.UNREAD_COUNT_CACHE_KEY)
            except Exception:
                pass

    @staticmethod
    async def mark_all_as_read():
        from app.modules.system.models import AdminNotification
        await AdminNotification.filter(is_read=False).update(is_read=True)
        try:
            redis = await get_redis_client()
            await redis.delete(AdminNotificationService.UNREAD_COUNT_CACHE_KEY)
        except Exception:
            pass
