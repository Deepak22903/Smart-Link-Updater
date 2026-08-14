import os
import asyncio
import random
import time
from typing import Optional
from urllib.parse import urlparse

import httpx

SCRAPER_API_URL = os.getenv("SCRAPER_API_URL")  # e.g., https://api.scraperapi.com
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

DEFAULT_HEADERS = {
    "User-Agent": os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# --- Politeness / anti-429 controls (override via env) -----------------------
# Max attempts per URL (1 initial try + retries) for transient failures.
MAX_ATTEMPTS = int(os.getenv("SCRAPER_MAX_ATTEMPTS", "4"))
# Minimum seconds between consecutive requests to the SAME host.
PER_HOST_MIN_INTERVAL = float(os.getenv("SCRAPER_PER_HOST_INTERVAL", "2.0"))
# Max in-flight requests to the SAME host (1 = fully serialized per host).
PER_HOST_CONCURRENCY = int(os.getenv("SCRAPER_PER_HOST_CONCURRENCY", "1"))
# Exponential backoff bounds (seconds) used when the server gives no Retry-After.
BACKOFF_BASE = float(os.getenv("SCRAPER_BACKOFF_BASE", "2.0"))
BACKOFF_MAX = float(os.getenv("SCRAPER_BACKOFF_MAX", "30.0"))

# Per-host throttle state. NOTE: this is per-process, so it throttles within a
# single Cloud Run instance. If the service scales to N instances the effective
# rate is up to N x this; keep min-instances low / concurrency high for batches,
# or move the throttle to a shared store (Redis) if you need a global cap.
_state_lock = asyncio.Lock()
_host_semaphores: dict[str, asyncio.Semaphore] = {}
_host_throttle_locks: dict[str, asyncio.Lock] = {}
_host_last_request: dict[str, float] = {}


def _host_of(url: str) -> str:
    return (urlparse(url).netloc or url).lower()


async def _host_primitives(host: str) -> tuple[asyncio.Semaphore, asyncio.Lock]:
    async with _state_lock:
        sem = _host_semaphores.setdefault(host, asyncio.Semaphore(PER_HOST_CONCURRENCY))
        lock = _host_throttle_locks.setdefault(host, asyncio.Lock())
    return sem, lock


async def _throttle(host: str, lock: asyncio.Lock) -> None:
    """Ensure at least PER_HOST_MIN_INTERVAL seconds between requests to `host`."""
    async with lock:
        last = _host_last_request.get(host, 0.0)
        wait = PER_HOST_MIN_INTERVAL - (time.monotonic() - last)
        if wait > 0:
            await asyncio.sleep(wait)
        _host_last_request[host] = time.monotonic()


def _backoff(attempt: int) -> float:
    """Exponential backoff with full jitter."""
    ceiling = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** attempt))
    return random.uniform(0, ceiling)


def _retry_after_seconds(response: httpx.Response) -> Optional[float]:
    """Parse a Retry-After header (delta-seconds or HTTP-date), if present."""
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        from datetime import datetime, timezone

        dt = parsedate_to_datetime(value)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


async def _fetch_once(url: str, timeout: float) -> httpx.Response:
    if SCRAPER_API_URL and SCRAPER_API_KEY:
        params = {"api_key": SCRAPER_API_KEY, "url": url, "render": "true"}
        async with httpx.AsyncClient(timeout=timeout, headers=DEFAULT_HEADERS) as client:
            return await client.get(SCRAPER_API_URL, params=params)
    async with httpx.AsyncClient(timeout=timeout, headers=DEFAULT_HEADERS) as client:
        return await client.get(url)


async def fetch_html(url: str, timeout: float = 30.0) -> str:
    """
    Fetch HTML from URL.

    Polite by design: caps concurrency and spaces out requests per host, retries
    only transient failures (429 / 5xx / network errors), honors `Retry-After`,
    and backs off with jitter. Non-transient errors (e.g. 404/403) are raised
    immediately. Raises the last exception if all attempts fail.
    """
    host = _host_of(url)
    sem, throttle_lock = await _host_primitives(host)
    last_exc: Optional[Exception] = None

    async with sem:  # cap in-flight requests to this host
        for attempt in range(MAX_ATTEMPTS):
            await _throttle(host, throttle_lock)  # space requests to this host

            delay: Optional[float] = None
            try:
                response = await _fetch_once(url, timeout)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status = exc.response.status_code
                if status == 429:
                    delay = _retry_after_seconds(exc.response)
                    if delay is None:
                        delay = _backoff(attempt)
                elif 500 <= status < 600:
                    delay = _backoff(attempt)
                else:
                    raise  # 4xx (404/403/etc.) -> not transient, don't retry
            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.PoolTimeout,
                httpx.RemoteProtocolError,
            ) as exc:
                last_exc = exc
                delay = _backoff(attempt)

            if attempt < MAX_ATTEMPTS - 1 and delay is not None:
                await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
