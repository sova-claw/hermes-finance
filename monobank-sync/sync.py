#!/usr/bin/env python3
"""Monobank → Maybe Finance transaction sync."""

import logging
import os
import time
from datetime import datetime, timezone

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MONOBANK_API = "https://api.monobank.ua"
MONOBANK_TOKEN = os.environ["MONOBANK_TOKEN"]
MAYBE_API_URL = os.environ["MAYBE_API_URL"].rstrip("/")
MAYBE_API_KEY = os.environ["MAYBE_API_KEY"]
# "mono_id1:maybe_id1,mono_id2:maybe_id2"
ACCOUNT_MAPPINGS = os.environ.get("ACCOUNT_MAPPINGS", "")
SYNC_INTERVAL_HOURS = int(os.environ.get("SYNC_INTERVAL_HOURS", "1"))
# Days to fetch on each run. Set to 90 for initial backfill, 2 for steady state.
FETCH_DAYS = int(os.environ.get("FETCH_DAYS", "2"))

# ISO 4217 numeric → alpha
CURRENCY_MAP = {
    980: "UAH",
    840: "USD",
    978: "EUR",
    826: "GBP",
    756: "CHF",
    985: "PLN",
    203: "CZK",
}

CHUNK_DAYS = 31  # Monobank statement max window
RATE_LIMIT_SLEEP = 65  # seconds between Monobank requests


def mono_headers() -> dict:
    return {"X-Token": MONOBANK_TOKEN}


def maybe_headers() -> dict:
    return {"X-Api-Key": MAYBE_API_KEY, "Content-Type": "application/json"}


def get_client_info() -> dict:
    r = httpx.get(f"{MONOBANK_API}/personal/client-info", headers=mono_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_statement(account_id: str, from_ts: int, to_ts: int) -> list:
    url = f"{MONOBANK_API}/personal/statement/{account_id}/{from_ts}/{to_ts}"
    r = httpx.get(url, headers=mono_headers(), timeout=30)
    if r.status_code == 429:
        log.warning("Rate limited by Monobank, sleeping 65s")
        time.sleep(RATE_LIMIT_SLEEP)
        r = httpx.get(url, headers=mono_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_maybe_accounts() -> list:
    r = httpx.get(f"{MAYBE_API_URL}/api/v1/accounts", headers=maybe_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("accounts", data) if isinstance(data, dict) else data


def post_transaction(maybe_account_id: str, tx: dict) -> bool:
    amount_minor = tx["amount"]  # kopecks / cents (signed)
    if amount_minor == 0:
        return True

    amount = abs(amount_minor) / 100.0
    nature = "income" if amount_minor > 0 else "expense"
    currency = CURRENCY_MAP.get(tx.get("currencyCode", 980), "UAH")
    date = datetime.fromtimestamp(tx["time"], tz=timezone.utc).strftime("%Y-%m-%d")
    name = tx.get("description") or tx.get("comment") or "Monobank"

    payload = {
        "transaction": {
            "account_id": maybe_account_id,
            "name": name,
            "date": date,
            "amount": amount,
            "nature": nature,
            "currency": currency,
            "external_id": f"monobank_{tx['id']}",
            "source": "monobank",
        }
    }

    r = httpx.post(
        f"{MAYBE_API_URL}/api/v1/transactions",
        headers=maybe_headers(),
        json=payload,
        timeout=30,
    )

    if r.status_code in (200, 201, 422):
        # 422 = duplicate (external_id already exists) — idempotent
        return True

    log.error("Failed to post tx %s: %s %s", tx["id"], r.status_code, r.text[:200])
    return False


def parse_mappings() -> dict:
    mappings = {}
    for pair in ACCOUNT_MAPPINGS.split(","):
        pair = pair.strip()
        if ":" in pair:
            mono_id, maybe_id = pair.split(":", 1)
            mappings[mono_id.strip()] = maybe_id.strip()
    return mappings


def sync_account(mono_id: str, maybe_id: str, fetch_days: int) -> None:
    now = int(datetime.now(timezone.utc).timestamp())
    end_ts = now
    remaining = fetch_days
    chunks = []

    while remaining > 0:
        days = min(CHUNK_DAYS, remaining)
        start_ts = end_ts - days * 86400
        chunks.append((start_ts, end_ts))
        end_ts = start_ts
        remaining -= days

    total = 0
    for i, (start_ts, end_ts) in enumerate(chunks):
        if i > 0:
            log.info("Sleeping %ds between Monobank requests (rate limit)", RATE_LIMIT_SLEEP)
            time.sleep(RATE_LIMIT_SLEEP)

        log.info("Fetching account=%s chunk %d/%d", mono_id, i + 1, len(chunks))
        try:
            txs = get_statement(mono_id, start_ts, end_ts)
        except httpx.HTTPStatusError as e:
            log.error("Statement fetch failed: %s", e)
            continue

        for tx in txs:
            if post_transaction(maybe_id, tx):
                total += 1

    log.info("account=%s synced %d transactions", mono_id, total)


def setup_mode() -> None:
    log.info("=== SETUP MODE — ACCOUNT_MAPPINGS not set ===")
    info = get_client_info()
    log.info("Monobank client: %s", info.get("name"))
    log.info("--- Monobank accounts ---")
    for acc in info.get("accounts", []):
        currency = CURRENCY_MAP.get(acc.get("currencyCode", 980), "?")
        balance = acc.get("balance", 0) / 100.0
        log.info(
            "  id=%-36s  type=%-12s  currency=%s  balance=%.2f  iban=%s",
            acc["id"],
            acc.get("type", "?"),
            currency,
            balance,
            acc.get("iban", ""),
        )
    log.info("--- Maybe Finance accounts ---")
    try:
        for acc in get_maybe_accounts():
            log.info(
                "  id=%-36s  name=%-30s  currency=%s",
                acc.get("id", "?"),
                acc.get("name", "?"),
                acc.get("currency", "?"),
            )
    except Exception as e:
        log.error("Could not fetch Maybe Finance accounts: %s", e)
    log.info("")
    log.info("Next step: create matching accounts in Maybe Finance UI, then set:")
    log.info("  ACCOUNT_MAPPINGS=<mono_id>:<maybe_id>,<mono_id2>:<maybe_id2>")
    log.info("Restart the service once ACCOUNT_MAPPINGS is set.")


def run() -> None:
    mappings = parse_mappings()
    if not mappings:
        setup_mode()
        return

    log.info("Syncing %d account(s), FETCH_DAYS=%d", len(mappings), FETCH_DAYS)
    for mono_id, maybe_id in mappings.items():
        sync_account(mono_id, maybe_id, FETCH_DAYS)
    log.info("Sync complete")


if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception:
            log.exception("Sync run failed")
        log.info("Sleeping %dh until next run", SYNC_INTERVAL_HOURS)
        time.sleep(SYNC_INTERVAL_HOURS * 3600)
