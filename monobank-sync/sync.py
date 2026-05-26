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
# Days to fetch on each run. MONOBANK_FETCH_DAYS overrides legacy FETCH_DAYS.
# Default 730 for initial backfill; set MONOBANK_FETCH_DAYS=2 in Railway for steady-state.
FETCH_DAYS = int(os.environ.get("MONOBANK_FETCH_DAYS", os.environ.get("FETCH_DAYS", "730")))

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

CHUNK_DAYS = 31       # Monobank statement max window
RATE_LIMIT_SLEEP = 65  # seconds between Monobank requests

# ---------------------------------------------------------------------------
# MCC → category name mapping
# ---------------------------------------------------------------------------
_MCC_RANGES: list[tuple] = [
    (range(5811, 5815), "Food & Drink"),   # restaurants, bars, fast food
    (range(5441, 5443), "Food & Drink"),   # candy/confectionery
    (range(5411, 5413), "Groceries"),      # grocery stores
    (range(5422, 5423), "Groceries"),      # meat provisioners
    (range(4111, 4114), "Transportation"), # local/suburban commuter transit
    ((5541, 5542), "Transportation"),      # gas stations
    (range(7512, 7514), "Transportation"), # car rentals
    (range(5912, 5913), "Healthcare"),     # drug stores / pharmacies
    (range(8011, 8099), "Healthcare"),     # medical services
    (range(5600, 5700), "Shopping"),       # clothing & accessories
    (range(5940, 5960), "Shopping"),       # hobby, toy, book stores
    (range(7832, 7835), "Entertainment"),  # cinemas
    (range(7991, 7995), "Entertainment"),  # amusement parks, sports
    (range(3000, 3350), "Travel"),         # airlines
    (range(7011, 7013), "Travel"),         # hotels/motels
    (range(5734, 5736), "Subscriptions"),  # computer/music stores
    (range(7372, 7380), "Subscriptions"),  # computer programming/services
]

_MCC_LOOKUP: dict[int, str] = {}
for _key, _cat in _MCC_RANGES:
    for _mcc in _key:
        _MCC_LOOKUP[_mcc] = _cat

CATEGORY_COLORS = {
    "Food & Drink":   "#f97316",
    "Groceries":      "#407706",
    "Transportation": "#0ea5e9",
    "Healthcare":     "#4da568",
    "Shopping":       "#3b82f6",
    "Entertainment":  "#a855f7",
    "Travel":         "#2563eb",
    "Subscriptions":  "#6366f1",
}

# In-memory cache: category name → Maybe Finance category id
_category_cache: dict[str, str] = {}

ACCOUNT_TYPE_NAMES = {
    "black": "Black",
    "white": "White",
    "fop":   "FOP",
    "eAid":  "eAid",
    "madeInUkraine": "Made in Ukraine",
    "iron":     "Iron",
    "platinum": "Platinum",
    "yellow":   "Yellow",
}

SYNC_ACCOUNT_TYPES = {"black", "white", "fop", "platinum", "iron", "yellow"}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def mono_headers() -> dict:
    return {"X-Token": MONOBANK_TOKEN}


def maybe_headers() -> dict:
    return {"X-Api-Key": MAYBE_API_KEY, "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Monobank API
# ---------------------------------------------------------------------------

def get_client_info() -> dict:
    r = httpx.get(f"{MONOBANK_API}/personal/client-info", headers=mono_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_statement(account_id: str, from_ts: int, to_ts: int) -> list:
    url = f"{MONOBANK_API}/personal/statement/{account_id}/{from_ts}/{to_ts}"
    r = httpx.get(url, headers=mono_headers(), timeout=30)
    if r.status_code == 429:
        log.warning("Rate limited by Monobank, sleeping %ds", RATE_LIMIT_SLEEP)
        time.sleep(RATE_LIMIT_SLEEP)
        r = httpx.get(url, headers=mono_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Maybe Finance API
# ---------------------------------------------------------------------------

def get_maybe_accounts() -> list:
    r = httpx.get(f"{MAYBE_API_URL}/api/v1/accounts", headers=maybe_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("accounts", data) if isinstance(data, dict) else data


def create_maybe_account(name: str, currency: str, balance: float) -> dict:
    payload = {
        "account": {
            "name": name,
            "currency": currency,
            "balance": balance,
            "accountable_type": "Depository",
        }
    }
    r = httpx.post(f"{MAYBE_API_URL}/api/v1/accounts", headers=maybe_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get_or_create_category(name: str) -> str | None:
    """Return Maybe Finance category id, creating it if necessary."""
    global _category_cache
    if not _category_cache:
        # Populate cache on first call
        try:
            r = httpx.get(f"{MAYBE_API_URL}/api/v1/categories", headers=maybe_headers(), timeout=30)
            r.raise_for_status()
            data = r.json()
            cats = data.get("categories", data) if isinstance(data, dict) else data
            for cat in cats:
                _category_cache[cat["name"]] = cat["id"]
        except Exception as e:
            log.warning("Failed to fetch categories: %s", e)
            return None

    if name in _category_cache:
        return _category_cache[name]

    color = CATEGORY_COLORS.get(name, "#737373")
    try:
        r = httpx.post(
            f"{MAYBE_API_URL}/api/v1/categories",
            headers=maybe_headers(),
            json={"category": {"name": name, "color": color}},
            timeout=30,
        )
        if r.status_code in (200, 201):
            cat_id = r.json().get("id")
            if cat_id:
                _category_cache[name] = cat_id
                return cat_id
        log.warning("Failed to create category %s: %s %s", name, r.status_code, r.text[:200])
    except Exception as e:
        log.warning("Exception creating category %s: %s", name, e)
    return None


def post_transaction(maybe_account_id: str, tx: dict) -> bool:
    amount_minor = tx["amount"]  # kopecks / cents (signed)
    if amount_minor == 0:
        return True

    amount = abs(amount_minor) / 100.0
    nature = "income" if amount_minor > 0 else "expense"
    currency = CURRENCY_MAP.get(tx.get("currencyCode", 980), "UAH")
    date = datetime.fromtimestamp(tx["time"], tz=timezone.utc).strftime("%Y-%m-%d")

    # Phase 2A: separate description (merchant name) from comment (user note)
    name = tx.get("description") or "Monobank"
    notes = tx.get("comment") or None

    # Phase 2B: MCC-based category
    category_id = None
    mcc = tx.get("mcc")
    if mcc:
        cat_name = _MCC_LOOKUP.get(int(mcc))
        if cat_name:
            category_id = get_or_create_category(cat_name)

    # Phase 3A: pending/hold flag + Phase 3B: foreign currency exchange rate
    extra: dict = {}
    if tx.get("hold"):
        extra["monobank"] = {"pending": True}

    operation_amount = tx.get("operationAmount")
    if operation_amount and abs(operation_amount) > 0 and abs(operation_amount) != abs(amount_minor):
        extra["exchange_rate"] = round(abs(amount_minor) / abs(operation_amount), 6)

    payload: dict = {
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
    if notes:
        payload["transaction"]["notes"] = notes
    if category_id:
        payload["transaction"]["category_id"] = category_id
    if extra:
        payload["transaction"]["extra"] = extra

    r = httpx.post(
        f"{MAYBE_API_URL}/api/v1/transactions",
        headers=maybe_headers(),
        json=payload,
        timeout=30,
    )

    if r.status_code in (200, 201):
        # Phase 3C: post cashback as a separate income transaction
        cashback = tx.get("cashbackAmount", 0)
        if cashback > 0:
            cb_payload = {
                "transaction": {
                    "account_id": maybe_account_id,
                    "name": f"Cashback: {name}",
                    "date": date,
                    "amount": cashback / 100.0,
                    "nature": "income",
                    "currency": currency,
                    "external_id": f"monobank_cashback_{tx['id']}",
                    "source": "monobank",
                }
            }
            rc = httpx.post(
                f"{MAYBE_API_URL}/api/v1/transactions",
                headers=maybe_headers(),
                json=cb_payload,
                timeout=30,
            )
            if rc.status_code not in (200, 201):
                log.warning("Cashback tx failed for %s: %s", tx["id"], rc.status_code)
        return True

    if r.status_code == 422:
        log.error("Validation error tx %s: %s %s", tx["id"], r.status_code, r.text[:400])
        return False

    log.error("Failed to post tx %s: %s %s", tx["id"], r.status_code, r.text[:200])
    return False


# ---------------------------------------------------------------------------
# Account mappings
# ---------------------------------------------------------------------------

def parse_mappings(raw: str = "") -> dict:
    mappings = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            mono_id, maybe_id = pair.split(":", 1)
            mappings[mono_id.strip()] = maybe_id.strip()
    return mappings


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

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
            log.info("Sleeping %ds between chunks (Monobank rate limit)", RATE_LIMIT_SLEEP)
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


# ---------------------------------------------------------------------------
# Auto setup
# ---------------------------------------------------------------------------

def auto_setup() -> None:
    """Auto-create Maybe Finance accounts for all Monobank accounts and print ACCOUNT_MAPPINGS."""
    log.info("=== AUTO SETUP — creating Maybe Finance accounts from Monobank ===")
    info = get_client_info()
    log.info("Monobank client: %s", info.get("name"))

    mono_accounts = [
        acc for acc in info.get("accounts", [])
        if acc.get("type") in SYNC_ACCOUNT_TYPES
    ]

    if not mono_accounts:
        log.warning("No syncable Monobank accounts found (types: %s)", SYNC_ACCOUNT_TYPES)
        return

    # Fetch existing Maybe Finance accounts to avoid creating duplicates on re-run.
    existing_by_name: dict[str, str] = {}
    try:
        for a in get_maybe_accounts():
            if a.get("name"):
                existing_by_name[a["name"]] = a["id"]
        log.info("Found %d existing Maybe Finance accounts", len(existing_by_name))
    except Exception as e:
        log.warning("Could not fetch existing accounts: %s", e)

    mappings = []
    for acc in mono_accounts:
        currency = CURRENCY_MAP.get(acc.get("currencyCode", 980), "UAH")
        acc_type = acc.get("type", "?")
        name = f"Monobank {ACCOUNT_TYPE_NAMES.get(acc_type, acc_type)} {currency}"

        if name in existing_by_name:
            maybe_id = existing_by_name[name]
            log.info("Reusing existing account: %s (id=%s)", name, maybe_id)
            mappings.append(f"{acc['id']}:{maybe_id}")
            continue

        # Use balance=0 so the opening anchor (placed 2 years back by Maybe Finance)
        # doesn't inflate the displayed balance when historical transactions are layered on top.
        # The correct balance emerges from importing the full transaction history.
        log.info("Creating Maybe Finance account: %s", name)
        try:
            created = create_maybe_account(name, currency, 0)
            maybe_id = created.get("id")
            log.info("  → created id=%s", maybe_id)
            mappings.append(f"{acc['id']}:{maybe_id}")
        except Exception as e:
            log.error("  → failed to create account %s: %s", name, e)

    if mappings:
        mapping_str = ",".join(mappings)
        log.info("")
        log.info("=== AUTO SETUP COMPLETE ===")
        log.info("Set this Railway variable and restart:")
        log.info("  ACCOUNT_MAPPINGS=%s", mapping_str)
        log.info("Also set FETCH_DAYS=365 for initial backfill (more history = more accurate balance).")
        log.info("Then change FETCH_DAYS back to 2 for steady-state.")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def discover_mappings() -> dict:
    """Build mono_id→maybe_id map by matching account names in Maybe Finance."""
    try:
        maybe_accounts = get_maybe_accounts()
    except Exception as e:
        log.warning("Could not fetch Maybe Finance accounts: %s", e)
        return {}

    maybe_by_name = {a["name"]: a["id"] for a in maybe_accounts}

    try:
        info = get_client_info()
    except Exception as e:
        log.warning("Could not fetch Monobank client info: %s", e)
        return {}

    mappings: dict = {}
    for acc in info.get("accounts", []):
        if acc.get("type") not in SYNC_ACCOUNT_TYPES:
            continue
        currency = CURRENCY_MAP.get(acc.get("currencyCode", 980), "UAH")
        acc_type = acc.get("type", "?")
        name = f"Monobank {ACCOUNT_TYPE_NAMES.get(acc_type, acc_type)} {currency}"
        maybe_id = maybe_by_name.get(name)
        if maybe_id:
            mappings[acc["id"]] = maybe_id
        else:
            log.warning("No Maybe Finance account for Monobank account: %s", name)
    return mappings


def run() -> None:
    # Prefer explicit ACCOUNT_MAPPINGS env var; fall back to auto-discovery by name.
    # Auto-discovery removes the deployment race condition that plagued the env var approach.
    mappings = parse_mappings(os.environ.get("ACCOUNT_MAPPINGS", ""))
    if not mappings:
        mappings = discover_mappings()

    if not mappings:
        auto_setup()
        return

    log.info("Syncing %d account(s), FETCH_DAYS=%d", len(mappings), FETCH_DAYS)
    for i, (mono_id, maybe_id) in enumerate(mappings.items()):
        if i > 0:
            log.info("Sleeping %ds between accounts (Monobank rate limit)", RATE_LIMIT_SLEEP)
            time.sleep(RATE_LIMIT_SLEEP)
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
