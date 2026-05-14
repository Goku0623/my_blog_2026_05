"""
一次性数据回填脚本：为已有 cover_image 但缺少缩略图的文章
生成 cover_image_thumb (400x225) 和 cover_image_large (1600x900)。

用法（在 backend 目录下执行）：
    python -m scripts.backfill_cover_image_variants
"""

import asyncio
import sys

from tortoise import Tortoise

from app.core.database import TORTOISE_ORM
from app.modules.articles.models import Article
from app.modules.articles.service import ArticleService


async def backfill() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        articles = await Article.filter(cover_image__not_isnull=True).all()
        total = len(articles)
        if total == 0:
            print("[backfill] no articles with cover_image, nothing to do.")
            return

        updated = 0
        skipped = 0
        failed = 0
        for index, article in enumerate(articles, start=1):
            if article.cover_image_thumb and article.cover_image_large:
                skipped += 1
                continue

            try:
                thumb, large = await ArticleService._generate_cover_variants(article.cover_image)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"[backfill] [{index}/{total}] article#{article.id} failed: {exc}")
                continue

            article.cover_image_thumb = thumb
            article.cover_image_large = large
            await article.save(update_fields=["cover_image_thumb", "cover_image_large"])
            updated += 1
            print(f"[backfill] [{index}/{total}] article#{article.id} updated.")

        print(
            f"[backfill] done. total={total}, updated={updated}, "
            f"skipped(already had variants)={skipped}, failed={failed}"
        )
    finally:
        await Tortoise.close_connections()


def main() -> int:
    try:
        asyncio.run(backfill())
        return 0
    except KeyboardInterrupt:
        print("[backfill] interrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
