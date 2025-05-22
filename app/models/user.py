from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class UserRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=True, default="viewer")
    
    # Relationships
    owned_events = relationship("Event", back_populates="owner")
    event_permissions = relationship("EventPermission", back_populates="user")
    event_changes = relationship("EventChange", back_populates="user") 