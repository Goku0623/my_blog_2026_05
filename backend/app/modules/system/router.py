from fastapi import APIRouter, Depends, Request, Query
from typing import Optional

from app.modules.system.schemas import (
    SiteConfigOut,
    SiteConfigUpdate,
    SiteConfigBulkUpdate,
    SensitiveWordCreate,
    SensitiveWordOut,
    OperationLogOut,
    OperationLogFilter,
    ScheduledTaskOut,
    ScheduledTaskUpdate,
)
from app.modules.system.service import (
    SiteConfigService,
    FeatureSwitchService,
    SensitiveWordService,
    OperationLogService,
    ScheduledTaskService,
)
from app.modules.auth.models import AdminUser
from app.core.dependencies import get_current_admin, get_client_ip
from app.common.response import success


router = APIRouter(tags=["System"])


@router.get("/system/configs/public", response_model=dict)
async def get_public_configs():
    configs = await SiteConfigService.get_public_configs()
    return success(configs, "获取公开配置成功")


@router.get("/admin/system/configs", response_model=dict)
async def get_all_configs(
    is_public_only: bool = Query(False),
    current_admin: AdminUser = Depends(get_current_admin)
):
    configs = await SiteConfigService.get_all_configs(is_public_only)
    config_list = [SiteConfigOut.model_validate(config) for config in configs]
    return success(config_list, "获取配置列表成功")


@router.put("/admin/system/configs/{key}", response_model=dict)
async def update_config(
    key: str,
    update_data: SiteConfigUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    config = await SiteConfigService.update_config(key, update_data.value, current_admin)
    return success(SiteConfigOut.model_validate(config), "更新配置成功")


@router.post("/admin/system/configs/bulk", response_model=dict)
async def bulk_update_configs(
    bulk_data: SiteConfigBulkUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    configs_dict = [{"key": c.key, "value": c.value} for c in bulk_data.configs]
    updated = await SiteConfigService.bulk_update_configs(configs_dict, current_admin)
    config_list = [SiteConfigOut.model_validate(config) for config in updated]
    return success(config_list, "批量更新配置成功")


@router.get("/admin/system/sensitive-words", response_model=dict)
async def list_sensitive_words(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin)
):
    words = await SensitiveWordService.list_sensitive_words(category, is_active)
    word_list = [SensitiveWordOut.model_validate(word) for word in words]
    return success(word_list, "获取敏感词列表成功")


@router.post("/admin/system/sensitive-words", response_model=dict)
async def create_sensitive_word(
    word_data: SensitiveWordCreate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    word = await SensitiveWordService.create_sensitive_word(word_data.word, word_data.category)
    return success(SensitiveWordOut.model_validate(word), "创建敏感词成功")


@router.delete("/admin/system/sensitive-words/{word_id}", response_model=dict)
async def delete_sensitive_word(
    word_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    await SensitiveWordService.delete_sensitive_word(word_id)
    return success(None, "删除敏感词成功")


@router.post("/admin/system/sensitive-words/refresh-cache", response_model=dict)
async def refresh_sensitive_words_cache(
    current_admin: AdminUser = Depends(get_current_admin)
):
    await SensitiveWordService.refresh_sensitive_words_cache()
    return success(None, "刷新敏感词缓存成功")


@router.get("/admin/system/logs", response_model=dict)
async def query_operation_logs(
    operator: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: AdminUser = Depends(get_current_admin)
):
    from datetime import datetime
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    logs, total = await OperationLogService.query_logs(
        operator, action, start_dt, end_dt, page, page_size
    )
    
    log_list = [OperationLogOut.model_validate(log) for log in logs]
    
    return success(
        {
            "items": log_list,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "获取操作日志成功"
    )


@router.get("/admin/system/tasks", response_model=dict)
async def list_scheduled_tasks(
    current_admin: AdminUser = Depends(get_current_admin)
):
    tasks = await ScheduledTaskService.list_tasks()
    task_list = [ScheduledTaskOut.model_validate(task) for task in tasks]
    return success(task_list, "获取定时任务列表成功")


@router.put("/admin/system/tasks/{task_id}", response_model=dict)
async def update_scheduled_task(
    task_id: int,
    update_data: ScheduledTaskUpdate,
    current_admin: AdminUser = Depends(get_current_admin)
):
    task = await ScheduledTaskService.update_task(
        task_id,
        update_data.is_active,
        update_data.cron_expression
    )
    return success(ScheduledTaskOut.model_validate(task), "更新定时任务成功")


@router.post("/admin/system/tasks/{task_id}/trigger", response_model=dict)
async def trigger_scheduled_task(
    task_id: int,
    current_admin: AdminUser = Depends(get_current_admin)
):
    task = await ScheduledTaskService.list_tasks()
    target_task = next((t for t in task if t.id == task_id), None)
    if not target_task:
        from app.common.exceptions import NotFoundException
        raise NotFoundException("定时任务不存在")
    
    result = await ScheduledTaskService.trigger_task_manually(target_task.name)
    return success(result, "触发定时任务成功")
