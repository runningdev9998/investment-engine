# SEC EDGAR Watchlist Filing Ingest + Dedupe

Python · PostgreSQL · SQLAlchemy · Alembic · Docker

---

## Quick Start (three commands)

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start PostgreSQL and run migrations
docker-compose up -d
alembic -c migrations/alembic.ini upgrade head

# 3. Run the ingestion script
python -m agents.agent_01_sec
```

> **Windows users:** use `copy .env.example .env` instead of `cp`.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker + Docker Compose | any recent version |

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Copy `.env.example` to `.env` and leave the defaults as-is for local development:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/investment_engine
SEC_USER_AGENT=Saman K research.robot90@gmail.com
```

No other values need to be changed for a local run.

---

## How to Clone and Run from Scratch

```bash
git clone <repo-url>
cd investment-engine

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # Mac/Linux

docker-compose up -d            # starts PostgreSQL on port 5432
alembic -c migrations/alembic.ini upgrade head  # creates tables + seeds watchlist rows

python -m agents.agent_01_sec   # first run: inserts new rows
python -m agents.agent_01_sec   # second run: all rows skipped (dedupe)
```

---

## Verifying the Dedupe Constraint

After the first run, connect to the database and check the row count:

```bash
docker exec -it investment_engine_db psql -U postgres -d investment_engine \
  -c "SELECT COUNT(*) FROM raw_events;"
```

Run the script a second time, then re-run the same query. The count must be
**identical** — zero new rows are added on subsequent runs for filings already
present.

To inspect the unique constraint directly:

```sql
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'raw_events'::regclass AND contype = 'u';
```

Expected output:

```
         conname          | contype
--------------------------+---------
 uq_raw_events_dedupe_key | u
```

Sample dedupe_key values:

```
AAPL|8-K|0000320193-26-000123
MSFT|4|0000789019-26-000456
```

---

## How to Add a New Ticker to the Watchlist

Connect to the database and insert a row:

```sql
INSERT INTO watchlist (ticker, company_name, cik, active)
VALUES ('GOOGL', 'Alphabet Inc.', '0001652044', true);
```

Then run the ingestion script again:

```bash
python -m agents.agent_01_sec
```

The new company's filings will be fetched and inserted on the next run.

---

## Project Structure

```
investment-engine/
  core/
    db.py              # SQLAlchemy engine + session factory
    fetcher.py         # HTTP client with retries and SEC headers
  agents/
    agent_01_sec.py    # ingestion script
  models/
    raw_events.py      # SQLAlchemy table definition
    watchlist.py       # SQLAlchemy table definition
  migrations/
    versions/
      0001_create_tables.py  # creates both tables + seeds watchlist
    env.py
    script.py.mako
    alembic.ini
  docker-compose.yml
  requirements.txt
  .env.example
  README.md
```

---

## Acceptance Criteria Verification

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | SEC User-Agent header correctly set | No 403 errors in logs; all requests succeed |
| 2 | At least one valid filing row after first run | `SELECT * FROM raw_events LIMIT 5;` |
| 3 | Re-running produces zero new rows | `SELECT COUNT(*) FROM raw_events;` identical after 2nd run |
| 4 | dedupe_key format correct | Confirm: `AAPL\|8-K\|0000320193-26-000123` |
| 5 | Clean run from fresh clone | Follow Quick Start above |

---

## Screenshots

First run:![1.jpg](1.jpg)
Second run:![2.jpg](2.jpg)


---

## Assumptions / Notes

- `source_url` is set to the filing **index page** (`-index.html`). The full-text
  `.txt` URL is also derivable from the same variables; index page was chosen as
  it is more human-readable and directly accessible.
- Sequential HTTP requests with a 0.5 s delay between calls to respect SEC rate
  limits (per `sec.gov/os/accessing-edgar-data`).
- `detected_at` is stored as UTC.
- The `processed` column defaults to `"NO"` to support a future processing pipeline.
