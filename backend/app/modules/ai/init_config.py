import os
from app.modules.system.models import SiteConfig


async def init_ai_configs():
    """
    从环境变量初始化 AI 相关配置到 SiteConfig 表
    如果配置已存在则不覆盖
    """
    configs = [
        {
            "key": "N8N_SECRET",
            "value": os.getenv("N8N_SECRET", "change_this_to_your_n8n_secret"),
            "value_type": SiteConfig.TYPE_STR,
            "description": "N8N 自动文章生成的验证密钥",
            "is_public": False,
        },
        {
            "key": "WEATHER_PROVIDER",
            "value": os.getenv("WEATHER_PROVIDER", "amap"),
            "value_type": SiteConfig.TYPE_STR,
            "description": "天气服务商 (amap/baidu/openweather)",
            "is_public": False,
        },
        {
            "key": "WEATHER_API_KEY",
            "value": os.getenv("WEATHER_API_KEY", ""),
            "value_type": SiteConfig.TYPE_STR,
            "description": "天气 API 密钥",
            "is_public": False,
        },
        {
            "key": "AI_API_KEY",
            "value": os.getenv("AI_API_KEY", ""),
            "value_type": SiteConfig.TYPE_STR,
            "description": "OpenAI 兼容 API 密钥",
            "is_public": False,
        },
        {
            "key": "AI_BASE_URL",
            "value": os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
            "value_type": SiteConfig.TYPE_STR,
            "description": "OpenAI 兼容 API 基础 URL",
            "is_public": False,
        },
        {
            "key": "AI_MODEL",
            "value": os.getenv("AI_MODEL", "gpt-3.5-turbo"),
            "value_type": SiteConfig.TYPE_STR,
            "description": "使用的 AI 模型名称",
            "is_public": False,
        },
    ]
    
    for config_data in configs:
        existing = await SiteConfig.get_or_none(key=config_data["key"])
        if not existing:
            await SiteConfig.create(**config_data)
            print(f"✓ 初始化配置: {config_data['key']}")
        else:
            print(f"- 配置已存在: {config_data['key']}")
