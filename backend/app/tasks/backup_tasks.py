import os
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from tortoise import Tortoise

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.database import TORTOISE_ORM


async def _init_db():
    await Tortoise.init(config=TORTOISE_ORM)


async def _close_db():
    await Tortoise.close_connections()


async def _backup_database_async():
    from app.modules.system.service import OperationLogService, SiteConfigService
    
    backup_dir_str = await SiteConfigService.get_config("BACKUP_DIR")
    backup_dir = Path(backup_dir_str or "./backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"blog_backup_{timestamp}.sql"
    
    try:
        db_url = settings.DATABASE_URL
        parts = db_url.replace("postgres://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_db[1]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        result = subprocess.run(
            [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", database,
                "-f", str(backup_file),
                "-F", "p",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            await OperationLogService.log_operation(
                operator="system",
                action="database_backup",
                target_type="backup",
                target_id=None,
                detail=f"Backup failed: {error_msg}",
                ip="127.0.0.1",
                result="failure"
            )
            return {"success": False, "error": error_msg}
        
        backup_files = sorted(backup_dir.glob("blog_backup_*.sql"), key=os.path.getmtime, reverse=True)
        if len(backup_files) > 7:
            for old_backup in backup_files[7:]:
                old_backup.unlink()
        
        await OperationLogService.log_operation(
            operator="system",
            action="database_backup",
            target_type="backup",
            target_id=None,
            detail=f"Backup created: {backup_file.name}",
            ip="127.0.0.1",
            result="success"
        )
        
        return {"success": True, "file": str(backup_file)}
        
    except subprocess.TimeoutExpired:
        await OperationLogService.log_operation(
            operator="system",
            action="database_backup",
            target_type="backup",
            target_id=None,
            detail="Backup timeout",
            ip="127.0.0.1",
            result="failure"
        )
        return {"success": False, "error": "Backup timeout"}
    except Exception as e:
        await OperationLogService.log_operation(
            operator="system",
            action="database_backup",
            target_type="backup",
            target_id=None,
            detail=f"Backup error: {str(e)}",
            ip="127.0.0.1",
            result="failure"
        )
        return {"success": False, "error": str(e)}


@celery_app.task(name="backup.database")
def backup_database():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_db())
        result = loop.run_until_complete(_backup_database_async())
        return result
    finally:
        loop.run_until_complete(_close_db())
        loop.close()
