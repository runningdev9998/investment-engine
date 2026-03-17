from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    cik = Column(String(10), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
