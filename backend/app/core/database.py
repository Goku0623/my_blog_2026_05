from tortoise import Tortoise
from app.core.config import settings


TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": [
                "app.modules.auth.models",
                "app.modules.articles.models",
                "app.modules.comments.models",
                "app.modules.guestbook.models",
                "app.modules.system.models",
                "app.modules.statistics.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()
