from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer
from datetime import datetime
import pytz

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(pytz.UTC).replace(tzinfo=None), nullable=False) 