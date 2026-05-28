"""Monobank HTTP client with automatic rate limiting and retry."""

import time
from typing import Any

import httpx
import structlog

log = structlog.get_logger(__name__)

# Monobank allows 1 request per 60s per token; +2s safety margin
_RATE_LIMIT_SECONDS = 62


class MonobankClient:
    """Thin HTTP wrapper for the Monobank personal API."""

    BASE_URL = "https://api.monobank.ua"

    def __init__(self, token: str, timeout: int = 30) -> None:
        self._headers = {"X-Token": token}
        self._http = httpx.Client(timeout=timeout)
        self._last_call_at: float | None = None

    def _wait_for_rate_limit(self) -> None:
        """Block until 62s have elapsed since the last successful API call."""
        if self._last_call_at is None:
            return
        elapsed = time.monotonic() - self._last_call_at
        wait = _RATE_LIMIT_SECONDS - elapsed
        if wait > 0:
            log.info("rate_limit_wait", seconds=round(wait, 1))
            time.sleep(wait)

    def _get(self, path: str) -> dict[str, Any] | list[Any]:
        """GET with retry on network errors and automatic 429 handling."""
        url = f"{self.BASE_URL}{path}"
        self._wait_for_rate_limit()

        for attempt in range(4):
            try:
                r = self._http.get(url, headers=self._headers)
                # only update on actual HTTP contact
                self._last_call_at = time.monotonic()
            except (
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                httpx.TimeoutException,
            ) as exc:
                if attempt == 3:
                    raise
                wait = 10 * (2**attempt)
                log.warning(
                    "request_retry",
                    error=str(exc),
                    attempt=attempt + 1,
                    wait=wait,
                )
                time.sleep(wait)
                continue

            if r.status_code == 429:
                log.warning("rate_limited", retry_in=_RATE_LIMIT_SECONDS)
                time.sleep(_RATE_LIMIT_SECONDS)
                # _last_call_at not reset: elapsed already covers the wait for next call
                continue

            r.raise_for_status()
            return r.json()  # type: ignore[no-any-return]

        raise RuntimeError("monobank api unavailable after retries")

    def get_client_info(self) -> dict[str, Any]:
        """Return client info including the account list."""
        return self._get("/personal/client-info")  # type: ignore[return-value]

    def get_statement(self, account_id: str, from_ts: int, to_ts: int) -> list[Any]:
        """Return transactions for account in the [from_ts, to_ts] window."""
        return self._get(f"/personal/statement/{account_id}/{from_ts}/{to_ts}")  # type: ignore[return-value]

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "MonobankClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
