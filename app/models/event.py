from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, JSON, TypeDecorator
from sqlalchemy.orm import relationship
from .base import BaseModel
import pytz
from datetime import datetime

class TZDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is not None:
                value = value.astimezone(pytz.UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = pytz.UTC.localize(value)
        return value

class Event(BaseModel):
    __tablename__ = "events"

    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    start_time = Column(TZDateTime, nullable=False)
    end_time = Column(TZDateTime, nullable=False)
    location = Column(String(200))
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # Stores the recurrence rule in JSON format
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_version = Column(Integer, default=1)
    
    # Relationships
    owner = relationship("User", back_populates="owned_events")
    permissions = relationship("EventPermission", back_populates="event", cascade="all, delete-orphan")
    versions = relationship("EventVersion", back_populates="event", cascade="all, delete-orphan")
    changes = relationship("EventChange", back_populates="event", cascade="all, delete-orphan")

class EventVersion(BaseModel):
    __tablename__ = "event_versions"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # Stores the complete event state at this version
    
    # Relationships
    event = relationship("Event", back_populates="versions")

class EventChange(BaseModel):
    __tablename__ = "event_changes"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_type = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    changes = Column(JSON, nullable=False)  # Stores the actual changes made
    
    # Relationships
    event = relationship("Event", back_populates="changes")
    user = relationship("User", back_populates="event_changes")

class EventPermission(BaseModel):
    __tablename__ = "event_permissions"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # OWNER, EDITOR, VIEWER
    
    # Relationships
    event = relationship("Event", back_populates="permissions")
    user = relationship("User", back_populates="event_permissions") 