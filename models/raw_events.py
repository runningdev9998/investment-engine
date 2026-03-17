from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, String, Text, UniqueConstraint

from models.watchlist import Base


class RawEvent(Base):
    __tablename__ = "raw_events"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_raw_events_dedupe_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    form_type = Column(String, nullable=False)
    filing_date = Column(Date, nullable=False)
    accession_number = Column(String, nullable=False)
    primary_document = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    dedupe_key = Column(String, nullable=False, unique=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed = Column(String, nullable=False, default="NO")
    notes = Column(Text, nullable=True)
