import os
import time

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

SEC_USER_AGENT = os.environ["SEC_USER_AGENT"]
SEC_BASE_URL = "https://data.sec.gov/submissions"

_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": SEC_USER_AGENT,
        "Accept": "application/json",
    }
)

_REQUEST_DELAY_SECONDS = 0.5


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_submissions(cik: str) -> dict:
    """Fetch the submissions JSON for a given zero-padded 10-digit CIK."""
    url = f"{SEC_BASE_URL}/CIK{cik}.json"
    response = _SESSION.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(_REQUEST_DELAY_SECONDS)
    return response.json()
