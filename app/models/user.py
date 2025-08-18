# C:\Users\Admin\Desktop\ai-mental-health-backend\app\models\user.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=True)
