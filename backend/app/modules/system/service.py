import json
from typing import Optional, List, Dict, Set
from datetime import datetime

from app.modules.system.models import SiteConfig, SensitiveWord, OperationLog, ScheduledTask
from app.modules.auth.models import AdminUser
from app.core.redis_client import get_redis_client
from app.common.exceptions import NotFoundException, BadRequestException


class SiteConfigService:
    CONFIG_CACHE_TTL = 300
    
    DEFAULT_CONFIGS = {
        "SITE_NAME": ("我的博客", "str", "站点名称", True),
        "SITE_DESCRIPTION": ("基于 FastAPI + Vue3 的现代化博客系统", "str", "站点描述", True),
        "SITE_KEYWORDS": ("博客,技术,分享,Vue,FastAPI", "str", "站点关键词", True),
        "SITE_AUTHOR": ("博主", "str", "站点作者", True),
        "SITE_LOGO": ("", "str", "站点Logo URL", True),
        "ICP_NUMBER": ("", "str", "ICP备案号", True),
        "COMMENT_ENABLED": ("true", "bool", "评论功能开关", True),
        "AI_ENABLED": ("true", "bool", "AI功能开关", True),
        "COMMENT_NEED_REVIEW": ("true", "bool", "评论需要审核", True),
        "COMMENT_RATE_LIMIT": ("5", "int", "评论速率限制（每分钟）", False),
        "AI_API_KEY": ("", "str", "AI API密钥", False),
        "AI_BASE_URL": ("", "str", "AI API地址", False),
        "AI_MODEL": ("", "str", "AI模型名称", False),
        "WEATHER_API_KEY": ("", "str", "天气API密钥", False),
        "WEATHER_PROVIDER": ("amap", "str", "天气服务商 (amap/baidu/openweather)", False),
        "WEATHER_API_BASE_URL": ("", "str", "天气 API 地址（可选，覆盖默认地址）", False),
        "N8N_SECRET": ("", "str", "N8N Webhook密钥", False),
        "ADMIN_EMAIL": ("", "str", "管理员邮箱", False),
        "SMTP_HOST": ("", "str", "SMTP服务器地址", False),
        "SMTP_PORT": ("587", "int", "SMTP端口", False),
        "SMTP_USER": ("", "str", "SMTP用户名", False),
        "SMTP_PASSWORD": ("", "str", "SMTP密码", False),
        "SMTP_FROM": ("", "str", "发件人地址", False),
        "BACKUP_DIR": ("./backups", "str", "备份目录", False),
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
    async def update_config(key: str, value: str, admin: AdminUser):
        config = await SiteConfig.get_or_none(key=key)
        if not config:
            raise NotFoundException(f"配置项 {key} 不存在")
        
        old_value = config.value
        config.value = value
        await config.save()
        
        redis = await get_redis_client()
        await redis.delete(f"config:{key}")
        
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
        for item in configs:
            key = item.get("key")
            value = item.get("value")
            if key and value is not None:
                config = await SiteConfig.get_or_none(key=key)
                if config:
                    config.value = value
                    await config.save()
                    
                    redis = await get_redis_client()
                    await redis.delete(f"config:{key}")
                    updated.append(config)
        
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
    async def get_public_configs() -> Dict[str, object]:
        """返回前端友好结构（snake_case 键名 + 类型转换）

        前端 SiteConfig 只关心一组固定字段，这里同时返回 raw 原始键值，
        方便管理端复用。
        """
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

        return {
            "site_name": _str("SITE_NAME", "我的博客"),
            "site_description": _str("SITE_DESCRIPTION", "一个现代化的博客系统"),
            "site_keywords": _str("SITE_KEYWORDS", "博客,技术,分享"),
            "site_author": _str("SITE_AUTHOR", "博主"),
            "site_logo": _str("SITE_LOGO", ""),
            "icp_number": _str("ICP_NUMBER", ""),
            "admin_email": _str("ADMIN_EMAIL", ""),
            "comment_enabled": _bool("COMMENT_ENABLED", True),
            "comment_audit_enabled": _bool("COMMENT_NEED_REVIEW", True),
            "ai_enabled": _bool("AI_ENABLED", True),
        }

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
