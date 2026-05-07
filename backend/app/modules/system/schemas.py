from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class SiteConfigOut(BaseModel):
    id: int
    key: str
    value: str
    value_type: str
    description: Optional[str] = None
    is_public: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SiteConfigUpdate(BaseModel):
    value: str


class ConfigItem(BaseModel):
    key: str
    value: str


class SiteConfigBulkUpdate(BaseModel):
    configs: List[ConfigItem]


class SensitiveWordCreate(BaseModel):
    word: str
    category: Optional[str] = None


class SensitiveWordOut(BaseModel):
    id: int
    word: str
    category: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationLogOut(BaseModel):
    id: int
    operator: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: str
    result: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationLogFilter(BaseModel):
    operator: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


class ScheduledTaskOut(BaseModel):
    id: int
    name: str
    task_path: str
    cron_expression: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskUpdate(BaseModel):
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = None


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]
