import asyncio
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tortoise import Tortoise

from app.tasks.celery_app import celery_app
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


async def _get_smtp_config():
    from app.modules.system.service import SiteConfigService
    
    smtp_host = await SiteConfigService.get_config("SMTP_HOST")
    smtp_port = await SiteConfigService.get_config("SMTP_PORT")
    smtp_user = await SiteConfigService.get_config("SMTP_USER")
    smtp_password = await SiteConfigService.get_config("SMTP_PASSWORD")
    smtp_from = await SiteConfigService.get_config("SMTP_FROM")
    
    return {
        "host": smtp_host or "smtp.gmail.com",
        "port": int(smtp_port) if smtp_port else 587,
        "user": smtp_user,
        "password": smtp_password,
        "from": smtp_from or smtp_user,
    }


def _send_email_sync(to: str, subject: str, body: str, smtp_config: dict):
    if not smtp_config["user"] or not smtp_config["password"]:
        return {"success": False, "error": "SMTP not configured"}
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_config["from"]
        msg["To"] = to
        
        html_part = MIMEText(body, "html", "utf-8")
        msg.attach(html_part)
        
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.send_message(msg)
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _send_new_comment_notification_async(comment_id: int):
    from app.modules.comments.models import Comment
    from app.modules.system.service import SiteConfigService
    
    comment = await Comment.get_or_none(id=comment_id).prefetch_related("article", "guest")
    if not comment:
        return {"success": False, "error": "Comment not found"}
    
    admin_email = await SiteConfigService.get_config("ADMIN_EMAIL")
    if not admin_email:
        return {"success": False, "error": "Admin email not configured"}
    
    article = await comment.article
    guest = await comment.guest
    
    subject = f"新评论通知 - {article.title}"
    body = f"""
    <html>
    <body>
        <h2>您的文章收到了新评论</h2>
        <p><strong>文章：</strong>{article.title}</p>
        <p><strong>评论者：</strong>{guest.nickname or "匿名"}</p>
        <p><strong>评论内容：</strong></p>
        <blockquote>{comment.content}</blockquote>
        <p><strong>评论时间：</strong>{comment.created_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><a href="http://localhost:3000/admin/comments/{comment.id}">查看详情</a></p>
    </body>
    </html>
    """
    
    smtp_config = await _get_smtp_config()
    result = _send_email_sync(admin_email, subject, body, smtp_config)
    
    return result


@celery_app.task(name="notification.send_new_comment_notification")
def send_new_comment_notification(comment_id: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_send_new_comment_notification_async(comment_id))
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()


async def _send_alert_email_async(subject: str, message: str):
    from app.modules.system.service import SiteConfigService
    
    admin_email = await SiteConfigService.get_config("ADMIN_EMAIL")
    if not admin_email:
        return {"success": False, "error": "Admin email not configured"}
    
    body = f"""
    <html>
    <body>
        <h2>系统告警通知</h2>
        <p>{message}</p>
        <p><strong>时间：</strong>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </body>
    </html>
    """
    
    smtp_config = await _get_smtp_config()
    result = _send_email_sync(admin_email, subject, body, smtp_config)
    
    return result


@celery_app.task(name="notification.send_alert_email")
def send_alert_email(subject: str, message: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_send_alert_email_async(subject, message))
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
