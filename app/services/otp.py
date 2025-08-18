import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from sqlalchemy.orm import Session
import aiosmtplib
from app.models.otp import OTP
from app.core.config import settings


def generate_otp(length: int = 6) -> str:
    """Generates the otp"""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def store_otp(db: Session, email: str, password: str, code: str, ttl_seconds: int = 300):
    """Stores the otp for verification"""
    expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    # If existing, overwrite
    otp_entry = db.query(OTP).filter_by(email=email).first()
    if otp_entry:
        otp_entry.code = code
        otp_entry.expires_at = expires
    else:
        otp_entry = OTP(email=email, code=code, password=password, expires_at=expires)
        db.add(otp_entry)

    db.commit()
