"""SEC EDGAR filing ingestion agent.

Reads active companies from the watchlist table, fetches their recent filings
from data.sec.gov, filters to allowed form types, and writes new rows to
raw_events using INSERT ... ON CONFLICT DO NOTHING for database-level dedup.
"""

import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Ensure the project root is importable when running as `python -m agents.agent_01_sec`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from core.db import SessionLocal
from core.fetcher import fetch_submissions
from models.raw_events import RawEvent
from models.watchlist import Watchlist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ALLOWED_FORM_TYPES = {"8-K", "4", "13D", "13D/A", "DEF 14A", "DEFA14A"}


def _build_source_url(cik: str, accession_number_with_dashes: str) -> str:
    cik_int = str(int(cik))
    acc_no_dash = accession_number_with_dashes.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}"
        f"/{acc_no_dash}/{accession_number_with_dashes}-index.html"
    )


def _normalise_accession(raw: str) -> str:
    """Return accession number with dashes (e.g. 0000320193-26-000123)."""
    raw = raw.strip()
    if len(raw) == 18 and "-" not in raw:
        return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"
    return raw


def run() -> None:
    session = SessionLocal()

    companies_processed = 0
    filings_found = 0
    rows_inserted = 0
    rows_skipped = 0

    try:
        watchlist = session.query(Watchlist).filter(Watchlist.active.is_(True)).all()

        if not watchlist:
            log.warning("No active companies found in the watchlist table.")
            return

        for company in watchlist:
            log.info("Processing %s (%s) — CIK %s", company.ticker, company.company_name, company.cik)
            companies_processed += 1

            try:
                data = fetch_submissions(company.cik)
            except Exception as exc:
                log.error("Failed to fetch submissions for %s: %s", company.ticker, exc)
                continue

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])

            for idx, form_type in enumerate(forms):
                if form_type not in ALLOWED_FORM_TYPES:
                    continue

                filings_found += 1

                raw_acc = accessions[idx] if idx < len(accessions) else ""
                accession_number = _normalise_accession(raw_acc)
                filing_date_str = dates[idx] if idx < len(dates) else ""
                primary_doc = primary_docs[idx] if idx < len(primary_docs) else None

                dedupe_key = f"{company.ticker}|{form_type}|{accession_number}"
                source_url = _build_source_url(company.cik, accession_number)

                try:
                    filing_date = date.fromisoformat(filing_date_str)
                except ValueError:
                    log.warning("Skipping filing with unparseable date '%s'", filing_date_str)
                    continue

                stmt = (
                    insert(RawEvent)
                    .values(
                        ticker=company.ticker,
                        company_name=company.company_name,
                        form_type=form_type,
                        filing_date=filing_date,
                        accession_number=accession_number,
                        primary_document=primary_doc or None,
                        source_url=source_url,
                        dedupe_key=dedupe_key,
                        detected_at=datetime.now(timezone.utc),
                        processed="NO",
                    )
                    .on_conflict_do_nothing(constraint="uq_raw_events_dedupe_key")
                )

                result = session.execute(stmt)
                session.commit()

                if result.rowcount == 1:
                    rows_inserted += 1
                    log.info("  NEW     %s", dedupe_key)
                else:
                    rows_skipped += 1
                    log.info("  SKIP    %s (duplicate)", dedupe_key)

    finally:
        session.close()

    print("\n" + "=" * 60)
    print("Run summary")
    print("=" * 60)
    print(f"  Companies processed : {companies_processed}")
    print(f"  Filings found       : {filings_found}")
    print(f"  New rows inserted   : {rows_inserted}")
    print(f"  Duplicates skipped  : {rows_skipped}")
    print("=" * 60)


if __name__ == "__main__":
    run()
