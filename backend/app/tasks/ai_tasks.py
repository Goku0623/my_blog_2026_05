import asyncio
import re
from datetime import datetime
from tortoise import Tortoise
import markdown

from app.tasks.celery_app import celery_app
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


def _generate_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug or "article"


async def _process_n8n_article_async(article_id: int):
    from app.modules.articles.models import Article
    
    article = await Article.get_or_none(id=article_id)
    if not article:
        return {"success": False, "error": "Article not found"}
    
    if not article.slug:
        base_slug = _generate_slug(article.title)
        slug = base_slug
        counter = 1
        while await Article.filter(slug=slug).exclude(id=article_id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        article.slug = slug
    
    if article.content and not article.rendered_content:
        md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code',
        ])
        article.rendered_content = md.convert(article.content)
    
    if not article.summary and article.content:
        plain_text = re.sub(r'[#*`\[\]()]', '', article.content)
        plain_text = re.sub(r'\n+', ' ', plain_text)
        words = plain_text.strip().split()
        article.summary = ' '.join(words[:50]) + ('...' if len(words) > 50 else '')
    
    if not article.published_at and article.status == Article.STATUS_PUBLISHED:
        article.published_at = datetime.now()
    
    await article.save()
    
    return {
        "success": True,
        "article_id": article.id,
        "slug": article.slug,
        "has_rendered_content": bool(article.rendered_content),
    }


@celery_app.task(name="ai.process_n8n_article")
def process_n8n_article(article_id: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_process_n8n_article_async(article_id))
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
