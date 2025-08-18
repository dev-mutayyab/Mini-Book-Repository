import uuid
from sqlalchemy import Column, String, Float, Date, TIMESTAMP
from app.db.session import Base


class Books(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()) , nullable=False)  # Auto-generate on insert
    title = Column(String)
    author = Column(String)
    price = Column(Float)
    publication_date = Column(Date)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
