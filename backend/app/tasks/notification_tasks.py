import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


async def _get_smtp_config() -> dict:
    from app.modules.system.service import SiteConfigService

    smtp_host = await SiteConfigService.get_config("SMTP_HOST") or os.getenv("SMTP_HOST", "")
    smtp_port = await SiteConfigService.get_config("SMTP_PORT") or os.getenv("SMTP_PORT", "")
    smtp_user = await SiteConfigService.get_config("SMTP_USER") or os.getenv("SMTP_USER", "")
    smtp_password = await SiteConfigService.get_config("SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD", "")
    smtp_from = await SiteConfigService.get_config("SMTP_FROM") or os.getenv("SMTP_FROM", "")

    config = {
        "host": smtp_host or "",
        "port": int(smtp_port) if smtp_port else 587,
        "user": smtp_user or "",
        "password": smtp_password or "",
        "from": smtp_from or smtp_user or "",
    }
    logger.info(
        "SMTP config: host=%s port=%s user=%s password=%s from=%s",
        config["host"], config["port"], config["user"],
        "***" if config["password"] else "(empty)",
        config["from"],
    )
    return config


def _send_email_sync(to: str, subject: str, html_body: str, smtp_config: dict) -> bool:
    if not smtp_config["host"]:
        logger.info("SMTP host not configured, skip sending email to %s", to)
        return False
    if not smtp_config["user"] or not smtp_config["password"]:
        logger.info("SMTP user/password not configured, skip sending email to %s", to)
        return False

    port = smtp_config["port"]
    use_ssl = port == 465
    logger.info(
        "Connecting to SMTP %s:%s as %s (mode=%s)",
        smtp_config["host"], port, smtp_config["user"],
        "SSL" if use_ssl else "STARTTLS",
    )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_config["from"]
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if use_ssl:
            with smtplib.SMTP_SSL(smtp_config["host"], port, timeout=15) as server:
                server.login(smtp_config["user"], smtp_config["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_config["host"], port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_config["user"], smtp_config["password"])
                server.send_message(msg)

        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


async def send_email(to: str, subject: str, html_body: str) -> bool:
    smtp_config = await _get_smtp_config()
    return await asyncio.to_thread(_send_email_sync, to, subject, html_body, smtp_config)


async def _get_admin_email() -> Optional[str]:
    from app.modules.system.service import SiteConfigService

    email = await SiteConfigService.get_config("ADMIN_EMAIL") or os.getenv("ADMIN_EMAIL", "")
    if email and email.strip():
        email = email.strip()
        logger.info("Admin email resolved from config: %s", email)
        return email

    from app.modules.auth.models import AdminUser
    admin = await AdminUser.filter(is_active=True).order_by("id").first()
    if admin and admin.email:
        logger.info("Admin email resolved from AdminUser: %s", admin.email)
        return admin.email.strip()

    logger.warning("Admin email not found in config or AdminUser table")
    return None


async def send_n8n_draft_email(article_title: str, article_id: int, article_slug: str) -> None:
    logger.info("N8N draft email: starting for article '%s' (id=%s)", article_title, article_id)

    admin_email = await _get_admin_email()
    if not admin_email:
        logger.warning("ADMIN_EMAIL not configured and no admin email found, skip N8N draft email")
        return

    logger.info("N8N draft email: admin_email=%s", admin_email)

    from app.modules.system.service import SiteConfigService
    site_url = (await SiteConfigService.get_config("SITE_URL") or "").strip().rstrip("/")
    edit_url = f"{site_url}/admin/articles/edit/{article_id}" if site_url else ""

    subject = f"[新草稿] N8N 自动生成文章：{article_title}"
    body = f"""<html><body>
<h2>N8N 工作流推送了新文章草稿</h2>
<p><strong>文章标题：</strong>{article_title}</p>
<p><strong>状态：</strong>草稿</p>"""
    if edit_url:
        body += f'<p><a href="{edit_url}">前往后台编辑发布</a></p>'
    body += "<p>请登录后台查看并编辑发布。</p>"
    body += "</body></html>"

    success = await send_email(admin_email, subject, body)
    if success:
        logger.info("N8N draft email: sent successfully to %s", admin_email)
    else:
        logger.error("N8N draft email: failed to send to %s", admin_email)


async def send_n8n_draft_email_safe(article_title: str, article_id: int, article_slug: str) -> None:
    try:
        await send_n8n_draft_email(article_title, article_id, article_slug)
    except Exception:
        logger.exception("N8N draft email: unhandled exception for article '%s' (id=%s)", article_title, article_id)


async def send_alert_email(subject: str, html_body: str) -> None:
    admin_email = await _get_admin_email()
    if not admin_email:
        logger.warning("ADMIN_EMAIL not configured and no admin email found, skip alert email")
        return

    await send_email(admin_email, f"[系统告警] {subject}", html_body)
