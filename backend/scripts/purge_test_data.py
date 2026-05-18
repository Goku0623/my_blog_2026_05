"""
清理测试数据脚本（保留管理员账号与系统配置）。

默认保留：
- admin_users（管理员账号）
- site_configs（系统配置）
- scheduled_tasks（任务配置）
- sensitive_words（敏感词库）

用法（在 backend 目录下执行）：
    python -m scripts.purge_test_data --yes
    python -m scripts.purge_test_data --yes --clear-uploads
"""

import argparse
import asyncio
import shutil
import sys
from pathlib import Path

from tortoise import Tortoise

from app.core.config import settings
from app.core.database import TORTOISE_ORM
from app.modules.articles.models import Article, ArticleDraftLink, ArticleTag, ArticleView, Category, Tag
from app.modules.auth.models import LoginAttempt, TokenBlacklist
from app.modules.comments.models import Comment, GuestIdentity
from app.modules.guestbook.models import GuestbookMessage
from app.modules.statistics.models import APICallLog, DailyStats
from app.modules.system.models import AdminNotification, OperationLog


async def _delete_model(model, label: str) -> int:
    deleted = await model.all().delete()
    print(f"[purge] {label}: deleted={deleted}")
    return deleted


def _purge_uploads() -> None:
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    if not upload_root.exists():
        print(f"[purge] uploads not found: {upload_root}")
        return

    removed_entries = 0
    for child in upload_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
            removed_entries += 1
        elif child.is_file():
            child.unlink()
            removed_entries += 1

    print(f"[purge] uploads cleared: path={upload_root}, removed_entries={removed_entries}")


async def purge(clear_uploads: bool) -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        print("[purge] start purging non-system test data...")

        # 先删除强依赖表，再删除主体表，避免外键约束问题。
        await _delete_model(ArticleDraftLink, "article_draft_links")
        await _delete_model(ArticleTag, "article_tags")
        await _delete_model(ArticleView, "article_views")
        await _delete_model(Comment, "comments")
        await _delete_model(GuestbookMessage, "guestbook_messages")
        await _delete_model(Article, "articles")
        await _delete_model(Category, "categories")
        await _delete_model(Tag, "tags")
        await _delete_model(GuestIdentity, "guest_identities")

        await _delete_model(APICallLog, "api_call_logs")
        await _delete_model(DailyStats, "daily_stats")
        await _delete_model(OperationLog, "operation_logs")
        await _delete_model(AdminNotification, "admin_notifications")
        await _delete_model(TokenBlacklist, "token_blacklist")
        await _delete_model(LoginAttempt, "login_attempts")

        if clear_uploads:
            _purge_uploads()

        print("[purge] done. preserved tables: admin_users, site_configs, scheduled_tasks, sensitive_words")
    finally:
        await Tortoise.close_connections()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Purge non-system test data while preserving admin and site configs.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required safety flag. Script will not run without this flag.",
    )
    parser.add_argument(
        "--clear-uploads",
        action="store_true",
        help="Also clear files under UPLOAD_DIR. Use with caution if configs reference media URLs.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.yes:
        parser.error("missing required flag: --yes")

    try:
        asyncio.run(purge(clear_uploads=args.clear_uploads))
        return 0
    except KeyboardInterrupt:
        print("[purge] interrupted")
        return 1


if __name__ == "__main__":
    sys.exit(main())
