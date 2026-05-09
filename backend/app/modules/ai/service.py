import json
import httpx
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from redis.asyncio import Redis

from app.common.exceptions import (
    BusinessException,
    NotFoundException,
    UnauthorizedException,
)
from app.modules.ai.schemas import (
    N8NArticlePayload,
    WeatherResponse,
    AICommentReplyRequest,
    AICommentReplyResponse,
)
from app.modules.articles.models import Article, Category, Tag, ArticleTag
from app.modules.system.models import SiteConfig
from app.modules.comments.models import Comment

SHENZHEN_CITY_CODE = "440300"
WEATHER_CACHE_PREFIX = f"weather:daily:amap:{SHENZHEN_CITY_CODE}"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


async def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    config = await SiteConfig.get_or_none(key=key)
    if config and config.value not in (None, ""):
        return config.value
    return os.getenv(key, default)


async def verify_n8n_secret(provided_secret: str) -> bool:
    expected_secret = await get_config_value("N8N_SECRET")
    if not expected_secret:
        raise BusinessException(500, "N8N 密钥未配置")
    return provided_secret == expected_secret


async def receive_n8n_article(payload: N8NArticlePayload) -> Article:
    if not await verify_n8n_secret(payload.n8n_secret):
        raise UnauthorizedException("N8N 密钥验证失败")
    
    category = None
    if payload.category_name:
        category = await Category.get_or_none(name=payload.category_name)
        if not category:
            category = await Category.create(
                name=payload.category_name,
                slug=payload.category_name.lower().replace(" ", "-"),
            )
    
    import re
    slug = re.sub(r'[^\w\s-]', '', payload.title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    existing_slug_count = await Article.filter(slug__startswith=slug).count()
    if existing_slug_count > 0:
        slug = f"{slug}-{existing_slug_count + 1}"
    
    article = await Article.create(
        title=payload.title,
        slug=slug,
        content=payload.content,
        summary=payload.summary,
        status=Article.STATUS_DRAFT,
        category=category,
    )
    
    for tag_name in payload.tags:
        tag = await Tag.get_or_none(name=tag_name)
        if not tag:
            tag_slug = re.sub(r'[^\w\s-]', '', tag_name.lower())
            tag_slug = re.sub(r'[-\s]+', '-', tag_slug).strip('-')
            tag = await Tag.create(name=tag_name, slug=tag_slug)
        
        await ArticleTag.create(article=article, tag=tag)
    
    return article


async def get_location_from_ip(ip: str) -> Optional[Dict[str, Any]]:
    if ip in ["127.0.0.1", "localhost", "unknown"]:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip}?lang=zh-CN")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "city": data.get("city"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                    }
    except Exception:
        pass
    
    return None


async def call_amap_weather(city: str, api_key: str, base_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """调用高德地图天气 API"""
    try:
        endpoint = f"{(base_url or 'https://restapi.amap.com').rstrip('/')}/v3/weather/weatherInfo"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                endpoint,
                params={
                    "key": api_key,
                    "city": city,
                    "extensions": "base",
                },
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get("status") != "1" or not data.get("lives"):
                return None
            
            live = data["lives"][0]
            return {
                "city": live.get("city", city),
                "temperature": float(live.get("temperature", 0)),
                "feels_like": float(live.get("temperature", 0)),
                "description": live.get("weather", "未知"),
                "humidity": int(live.get("humidity", 0)),
                "wind_speed": _parse_wind_speed(live.get("windpower", "0")),
                "icon": "01d",
                "updated_at": datetime.now(SHANGHAI_TZ),
            }
    except Exception:
        return None


async def call_baidu_weather(lat: float, lon: float, api_key: str, base_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """调用百度地图天气 API"""
    try:
        endpoint = f"{(base_url or 'https://api.map.baidu.com').rstrip('/')}/weather/v1/"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                endpoint,
                params={
                    "ak": api_key,
                    "location": f"{lon},{lat}",
                    "data_type": "all",
                },
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get("status") != 0 or not data.get("result"):
                return None
            
            now = data["result"]["now"]
            return {
                "city": data["result"]["location"]["name"],
                "temperature": float(now.get("temp", 0)),
                "feels_like": float(now.get("feels_like", 0)),
                "description": now.get("text", "未知"),
                "humidity": int(now.get("rh", 0)),
                "wind_speed": float(now.get("wind_speed", 0)),
                "icon": "01d",
                "updated_at": datetime.now(SHANGHAI_TZ),
            }
    except Exception:
        return None


async def call_openweather_api(lat: float, lon: float, api_key: str, base_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """调用 OpenWeatherMap API"""
    try:
        endpoint = f"{(base_url or 'https://api.openweathermap.org').rstrip('/')}/data/2.5/weather"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                endpoint,
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return {
                "city": data.get("name", "未知"),
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"],
                "updated_at": datetime.now(SHANGHAI_TZ),
            }
    except Exception:
        return None


def _parse_wind_speed(wind_power: str) -> float:
    """解析高德风力等级为风速（m/s）"""
    wind_map = {
        "≤3": 3.3, "4": 7.9, "5": 10.7, "6": 13.8,
        "7": 17.1, "8": 20.7, "9": 24.4, "10": 28.4,
    }
    return wind_map.get(wind_power, 0.0)


async def get_weather(
    ip: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    city: Optional[str] = None,
    redis: Optional[Redis] = None,
) -> WeatherResponse:
    api_key = await get_config_value("WEATHER_API_KEY")
    weather_api_base_url = await get_config_value("WEATHER_API_BASE_URL")

    if not api_key:
        raise BusinessException(500, "天气 API 密钥未配置")

    # 锁定深圳：只使用高德城市编码 440300，缓存维度按“天”组织。
    date_key = datetime.now(SHANGHAI_TZ).strftime("%Y%m%d")
    today_cache_key = f"{WEATHER_CACHE_PREFIX}:{date_key}"
    latest_cache_key = f"{WEATHER_CACHE_PREFIX}:latest"

    if redis:
        cached = await redis.get(today_cache_key)
        if cached:
            return WeatherResponse(**json.loads(cached))

    weather_data = await call_amap_weather(SHENZHEN_CITY_CODE, api_key, weather_api_base_url)

    if not weather_data:
        if redis:
            latest_cached = await redis.get(latest_cache_key)
            if latest_cached:
                return WeatherResponse(**json.loads(latest_cached))
        raise BusinessException(500, "天气 API 调用失败")

    weather_response = WeatherResponse(**weather_data)

    if redis:
        weather_json = json.dumps(weather_response.model_dump(), default=str)
        # 保留 3 天便于容灾；latest 便于兜底快速读取。
        await redis.setex(today_cache_key, 3 * 24 * 60 * 60, weather_json)
        await redis.setex(latest_cache_key, 3 * 24 * 60 * 60, weather_json)

    return weather_response


async def check_ai_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    redis: Redis
) -> bool:
    current = await redis.get(key)
    if current is None:
        await redis.setex(key, window_seconds, 1)
        return True
    else:
        count = int(current)
        if count >= limit:
            return False
        await redis.incr(key)
        return True


async def call_openai_api(
    messages: List[Dict[str, str]],
    redis: Redis,
) -> Dict[str, Any]:
    api_key = await get_config_value("AI_API_KEY")
    base_url = await get_config_value("AI_BASE_URL", "https://api.openai.com/v1")
    model = await get_config_value("AI_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        raise BusinessException(500, "AI API 密钥未配置")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                },
            )
            
            if response.status_code != 200:
                raise BusinessException(500, f"AI API 调用失败: {response.text}")
            
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "tokens": data["usage"]["total_tokens"],
            }
            
    except httpx.HTTPError as e:
        raise BusinessException(500, f"AI API 请求失败: {str(e)}")


async def generate_comment_reply(
    request: AICommentReplyRequest,
    admin_username: str,
    redis: Redis,
) -> AICommentReplyResponse:
    rate_limit_key = f"ai_comment_reply:{admin_username}"
    if not await check_ai_rate_limit(rate_limit_key, 20, 60, redis):
        raise BusinessException(429, "AI 调用过于频繁，请稍后再试")
    
    comment = await Comment.get_or_none(id=request.comment_id)
    if not comment:
        raise NotFoundException("评论不存在")
    
    context = "\n".join(request.context_comments) if request.context_comments else ""
    
    messages = [
        {
            "role": "system",
            "content": "你是一个友好的博客管理员助手，负责回复用户评论。请生成专业、友好且有帮助的回复。",
        },
        {
            "role": "user",
            "content": f"文章标题：{request.article_title}\n\n用户评论：{request.comment_content}\n\n上下文：{context}\n\n请生成一个合适的回复。",
        },
    ]
    
    result = await call_openai_api(messages, redis)
    
    return AICommentReplyResponse(
        suggested_reply=result["content"],
        model_used=result["model"],
        tokens_used=result["tokens"],
    )
