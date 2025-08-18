from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class CreateBook(BaseModel):
    title: str
    author: str
    price: float
    publication_date: date


class UpdateBook(BaseModel):
    title: Optional[str]
    author: Optional[str]
    price: Optional[float]
    publication_date: Optional[date]


class ShowBook(BaseModel):
    id: str
    title: str
    author: str
    price: float
    publication_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShowBookList(BaseModel):
    books: list[ShowBook]
    total: int
    offset: int
    limit: int

    class Config:
        from_attributes = True
