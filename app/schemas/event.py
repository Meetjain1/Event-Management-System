from pydantic import BaseModel, constr
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..models.user import UserRole

class RecurrencePattern(BaseModel):
    frequency: str  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int = 1
    until: Optional[datetime] = None
    count: Optional[int] = None
    by_day: Optional[List[str]] = None
    by_month: Optional[List[int]] = None
    by_monthday: Optional[List[int]] = None

class EventBase(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=200)] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None

class EventInDB(EventBase):
    id: int
    owner_id: int
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Event(EventInDB):
    pass

class EventVersion(BaseModel):
    id: int
    event_id: int
    version_number: int
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class EventChange(BaseModel):
    id: int
    event_id: int
    user_id: int
    version_number: int
    change_type: str
    changes: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class EventPermission(BaseModel):
    id: int
    event_id: int
    user_id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class EventPermissionCreate(BaseModel):
    user_id: int
    role: UserRole

class EventPermissionUpdate(BaseModel):
    role: UserRole

class EventDiff(BaseModel):
    field: str
    old_value: Any
    new_value: Any 