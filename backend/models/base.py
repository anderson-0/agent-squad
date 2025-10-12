"""
SQLAlchemy Base Model
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
