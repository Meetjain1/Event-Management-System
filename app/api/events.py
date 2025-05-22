from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import List, Optional, Any
from datetime import datetime
import pytz
import json
from dateutil.parser import parse

from ..core.security import get_current_user
from ..core.database import get_db
from ..schemas.event import (
    Event,
    EventCreate,
    EventUpdate,
    EventPermission,
    EventPermissionCreate,
    EventVersion,
    EventChange,
    EventDiff
)
from ..models.event import (
    Event as EventModel,
    EventPermission as EventPermissionModel,
    EventVersion as EventVersionModel,
    EventChange as EventChangeModel
)
from ..models.user import User, UserRole

router = APIRouter()

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def convert_to_ist(dt: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    if dt.tzinfo is None:  # if naive datetime
        dt = pytz.utc.localize(dt)
    return dt.astimezone(IST)

def convert_to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC and remove timezone info"""
    if isinstance(dt, str):
        dt = parse(dt)
    if dt.tzinfo is None:  # if naive datetime
        dt = IST.localize(dt)
    utc_dt = dt.astimezone(pytz.utc)
    return utc_dt.replace(tzinfo=None)  # Remove timezone info for database storage

def serialize_datetime(obj):
    """Helper function to serialize datetime objects to ISO format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

async def check_event_permission(
    event_id: int,
    user: User,
    db: AsyncSession,
    required_role: UserRole = UserRole.VIEWER
) -> EventModel:
    """Check if user has required permission for the event."""
    stmt = select(EventModel).where(EventModel.id == event_id)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.owner_id == user.id:
        return event
    
    stmt = select(EventPermissionModel).where(
        and_(
            EventPermissionModel.event_id == event_id,
            EventPermissionModel.user_id == user.id
        )
    )
    result = await db.execute(stmt)
    permission = result.scalar_one_or_none()
    
    if not permission or UserRole[permission.role].value < required_role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return event


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create new event."""
    event_data = event_in.dict()
    
    # Convert times to UTC without timezone info for storage
    start_time = convert_to_utc(event_data['start_time'])
    end_time = convert_to_utc(event_data['end_time'])
    
    # Handle recurrence pattern datetime serialization
    recurrence_pattern = None
    if event_data.get('recurrence_pattern'):
        recurrence = event_data['recurrence_pattern'].copy()
        if isinstance(recurrence, dict) and recurrence.get('until'):
            until_dt = convert_to_utc(recurrence['until'])
            recurrence['until'] = until_dt.isoformat()
        recurrence_pattern = recurrence
    
    # Create event
    event = EventModel(
        title=event_data['title'],
        description=event_data.get('description'),
        start_time=start_time,
        end_time=end_time,
        location=event_data.get('location'),
        is_recurring=event_data.get('is_recurring', False),
        recurrence_pattern=recurrence_pattern,
        owner_id=current_user.id,
        current_version=1
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Create initial version with serialized data
    version_data = {
        'title': event.title,
        'description': event.description,
        'start_time': event.start_time.isoformat() if event.start_time else None,
        'end_time': event.end_time.isoformat() if event.end_time else None,
        'location': event.location,
        'is_recurring': event.is_recurring,
        'recurrence_pattern': event.recurrence_pattern
    }
    
    version = EventVersionModel(
        event_id=event.id,
        version_number=1,
        data=version_data
    )
    db.add(version)
    
    # Record change
    change = EventChangeModel(
        event_id=event.id,
        user_id=current_user.id,
        version_number=1,
        change_type="CREATE",
        changes=version_data
    )
    db.add(change)
    
    await db.commit()
    
    # Convert times back to IST for response
    event.start_time = convert_to_ist(event.start_time) if event.start_time else None
    event.end_time = convert_to_ist(event.end_time) if event.end_time else None
    return event


@router.get("", response_model=List[Event])
async def list_events(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List events user has access to."""
    stmt = select(EventModel).where(
        or_(
            EventModel.owner_id == current_user.id,
            EventModel.id.in_(
                select(EventPermissionModel.event_id).where(
                    EventPermissionModel.user_id == current_user.id
                )
            )
        )
    )
    
    if start_date:
        stmt = stmt.where(EventModel.start_time >= start_date)
    if end_date:
        stmt = stmt.where(EventModel.end_time <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    # Convert times to IST for response
    for event in events:
        event.start_time = convert_to_ist(event.start_time) if event.start_time else None
        event.end_time = convert_to_ist(event.end_time) if event.end_time else None
    
    return events


@router.get("/{event_id}", response_model=Event)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get event by ID."""
    event = await check_event_permission(event_id, current_user, db)
    
    # Convert times to IST for response
    event.start_time = convert_to_ist(event.start_time) if event.start_time else None
    event.end_time = convert_to_ist(event.end_time) if event.end_time else None
    
    return event


@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update event."""
    event = await check_event_permission(event_id, current_user, db, UserRole.EDITOR)
    
    old_data = {
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "is_recurring": event.is_recurring,
        "recurrence_pattern": event.recurrence_pattern
    }
    
    update_data = event_in.dict(exclude_unset=True)
    
    # Handle datetime fields
    if 'start_time' in update_data:
        update_data['start_time'] = convert_to_utc(update_data['start_time'])
    if 'end_time' in update_data:
        update_data['end_time'] = convert_to_utc(update_data['end_time'])
    
    # Handle recurrence pattern
    if 'recurrence_pattern' in update_data and update_data['recurrence_pattern']:
        recurrence = update_data['recurrence_pattern'].copy()
        if isinstance(recurrence, dict) and recurrence.get('until'):
            until_dt = convert_to_utc(recurrence['until'])
            recurrence['until'] = until_dt.isoformat()
        update_data['recurrence_pattern'] = recurrence
    
    # Update event fields
    for field, value in update_data.items():
        setattr(event, field, value)
    
    event.current_version += 1
    
    # Create version with serialized data
    version_data = {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in update_data.items()
    }
    
    version = EventVersionModel(
        event_id=event.id,
        version_number=event.current_version,
        data=version_data
    )
    db.add(version)
    
    # Record changes with serialized datetime values
    changes = {
        k: {
            "old": old_data.get(k),
            "new": v.isoformat() if isinstance(v, datetime) else v
        }
        for k, v in update_data.items()
        if old_data.get(k) != v
    }
    
    change = EventChangeModel(
        event_id=event.id,
        user_id=current_user.id,
        version_number=event.current_version,
        change_type="UPDATE",
        changes=changes
    )
    db.add(change)
    
    await db.commit()
    await db.refresh(event)
    
    # Convert times to IST for response
    event.start_time = convert_to_ist(event.start_time) if event.start_time else None
    event.end_time = convert_to_ist(event.end_time) if event.end_time else None
    return event


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete event."""
    event = await check_event_permission(event_id, current_user, db, UserRole.OWNER)
    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted successfully"}


@router.post("/{event_id}/share", response_model=EventPermission)
async def share_event(
    event_id: int,
    permission_in: EventPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Share event with another user."""
    event = await check_event_permission(event_id, current_user, db, UserRole.OWNER)
    
    # Check if permission already exists
    stmt = select(EventPermissionModel).where(
        and_(
            EventPermissionModel.event_id == event_id,
            EventPermissionModel.user_id == permission_in.user_id
        )
    )
    result = await db.execute(stmt)
    existing_permission = result.scalar_one_or_none()
    
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists"
        )
    
    permission = EventPermissionModel(
        event_id=event_id,
        user_id=permission_in.user_id,
        role=permission_in.role
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


@router.get("/{event_id}/history/{version_id}", response_model=EventVersion)
async def get_event_version(
    event_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get specific version of an event."""
    await check_event_permission(event_id, current_user, db)
    
    stmt = select(EventVersionModel).where(
        and_(
            EventVersionModel.event_id == event_id,
            EventVersionModel.version_number == version_id
        )
    )
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return version


@router.get("/{event_id}/changelog", response_model=List[EventChange])
async def get_event_changelog(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get changelog for an event."""
    await check_event_permission(event_id, current_user, db)
    
    stmt = select(EventChangeModel).where(
        EventChangeModel.event_id == event_id
    ).order_by(EventChangeModel.version_number.desc())
    
    result = await db.execute(stmt)
    changes = result.scalars().all()
    
    return changes


@router.get("/{event_id}/diff/{version_id1}/{version_id2}", response_model=List[EventDiff])
async def get_event_diff(
    event_id: int,
    version_id1: int,
    version_id2: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get diff between two versions of an event."""
    await check_event_permission(event_id, current_user, db)
    
    # Get first version
    stmt = select(EventVersionModel).where(
        and_(
            EventVersionModel.event_id == event_id,
            EventVersionModel.version_number == version_id1
        )
    )
    result = await db.execute(stmt)
    v1 = result.scalar_one_or_none()
    
    # Get second version
    stmt = select(EventVersionModel).where(
        and_(
            EventVersionModel.event_id == event_id,
            EventVersionModel.version_number == version_id2
        )
    )
    result = await db.execute(stmt)
    v2 = result.scalar_one_or_none()
    
    if not v1 or not v2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found"
        )
    
    diffs = []
    all_fields = set(v1.data.keys()) | set(v2.data.keys())
    
    for field in all_fields:
        old_value = v1.data.get(field)
        new_value = v2.data.get(field)
        if old_value != new_value:
            diffs.append(EventDiff(
                field=field,
                old_value=old_value,
                new_value=new_value
            ))
    
    return diffs
