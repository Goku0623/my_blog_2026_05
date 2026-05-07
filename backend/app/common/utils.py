import hashlib
import secrets
import re
from datetime import datetime
from typing import Optional, Tuple, List
from tortoise.queryset import QuerySet


def generate_random_string(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_current_timestamp() -> int:
    return int(datetime.now().timestamp())


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    if dt is None:
        return None
    return dt.strftime(fmt)


async def paginate_queryset(
    queryset: QuerySet, 
    page: int = 1, 
    page_size: int = 10
) -> Tuple[List, int]:
    total = await queryset.count()
    offset = (page - 1) * page_size
    items = await queryset.offset(offset).limit(page_size)
    return items, total


def generate_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    return slug[:200]


def sanitize_markdown(content: str) -> str:
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
    ]
    
    sanitized = content
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized
