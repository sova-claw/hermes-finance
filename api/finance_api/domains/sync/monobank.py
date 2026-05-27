"""Monobank → PostgreSQL transaction sync."""
import time
import uuid
from datetime import date, datetime, timezone

import httpx
import structlog
from sqlmodel import Session, select

from finance_api.core.config import settings
from finance_api.core.db.engine import engine
from finance_api.domains.accounts.models import Account
from finance_api.domains.sync.models import SyncRun
from finance_api.domains.transactions.models import Transaction

log = structlog.get_logger(__name__)

MONOBANK_API = "https://api.monobank.ua"
CHUNK_DAYS = 31
RATE_LIMIT_SLEEP = 65

CURRENCY_MAP = {
    980: "UAH", 840: "USD", 978: "EUR",
    826: "GBP", 756: "CHF", 985: "PLN", 203: "CZK",
}

SYNC_ACCOUNT_TYPES = {"black", "white", "fop", "platinum", "iron", "yellow"}

ACCOUNT_TYPE_NAMES = {
    "black": "Black", "white": "White", "fop": "FOP",
    "iron": "Iron", "platinum": "Platinum", "yellow": "Yellow",
}

_MCC_RANGES: list[tuple] = [
    (range(5811, 5815), "Food & Drink"),
    (range(5441, 5443), "Food & Drink"),
    (range(5411, 5413), "Groceries"),
    (range(5422, 5423), "Groceries"),
    (range(4111, 4114), "Transportation"),
    ((5541, 5542), "Transportation"),
    (range(7512, 7514), "Transportation"),
    (range(5912, 5913), "Healthcare"),
    (range(8011, 8099), "Healthcare"),
    (range(5600, 5700), "Shopping"),
    (range(5940, 5960), "Shopping"),
    (range(7832, 7835), "Entertainment"),
    (range(7991, 7995), "Entertainment"),
    (range(3000, 3350), "Travel"),
    (range(7011, 7013), "Travel"),
    (range(5734, 5736), "Subscriptions"),
    (range(7372, 7380), "Subscriptions"),
]
MCC_LOOKUP: dict[int, str] = {
    mcc: cat for rng, cat in _MCC_RANGES for mcc in rng
}


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    for attempt in range(4):
        try:
            return getattr(httpx, method)(url, timeout=30, **kwargs)
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException) as exc:
            if attempt == 3:
                raise
            wait = 10 * (2**attempt)
            log.warning("request_failed", error=str(exc), attempt=attempt + 1, retry_in=wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def _mono_headers() -> dict[str, str]:
    return {"X-Token": settings.monobank_token}


def get_client_info() -> dict:
    r = _request("get", f"{MONOBANK_API}/personal/client-info", headers=_mono_headers())
    r.raise_for_status()
    return r.json()


def get_statement(account_id: str, from_ts: int, to_ts: int) -> list:
    url = f"{MONOBANK_API}/personal/statement/{account_id}/{from_ts}/{to_ts}"
    r = _request("get", url, headers=_mono_headers())
    if r.status_code == 429:
        log.warning("rate_limited", sleep=RATE_LIMIT_SLEEP)
        time.sleep(RATE_LIMIT_SLEEP)
        r = _request("get", url, headers=_mono_headers())
    r.raise_for_status()
    return r.json()


def _upsert_account(session: Session, mono_id: str, name: str, currency: str, account_type: str, balance: float) -> Account:
    existing = session.exec(select(Account).where(Account.monobank_id == mono_id)).first()
    if existing:
        existing.balance = balance
        existing.synced_at = datetime.utcnow()
        session.add(existing)
        return existing
    account = Account(
        monobank_id=mono_id,
        name=name,
        currency=currency,
        account_type=account_type,
        balance=balance,
        synced_at=datetime.utcnow(),
    )
    session.add(account)
    session.flush()
    return account


def _import_transaction(session: Session, account_id: uuid.UUID, tx: dict) -> bool:
    amount_minor = tx["amount"]
    if amount_minor == 0:
        return False

    monobank_id = f"monobank_{tx['id']}"
    if session.exec(select(Transaction).where(Transaction.monobank_id == monobank_id)).first():
        return False  # already imported

    amount = abs(amount_minor) / 100.0
    if amount_minor < 0:
        amount = -amount  # expenses are negative

    currency = CURRENCY_MAP.get(tx.get("currencyCode", 980), "UAH")
    tx_date = date.fromtimestamp(tx["time"])
    description = tx.get("description") or "Monobank"
    notes = tx.get("comment") or None
    mcc = int(tx["mcc"]) if tx.get("mcc") else None
    category = MCC_LOOKUP.get(mcc) if mcc else None

    extra: dict = {}
    if tx.get("hold"):
        extra["pending"] = True
    op_amount = tx.get("operationAmount")
    if op_amount and abs(op_amount) > 0 and abs(op_amount) != abs(amount_minor):
        extra["exchange_rate"] = round(abs(amount_minor) / abs(op_amount), 6)

    session.add(Transaction(
        account_id=account_id,
        monobank_id=monobank_id,
        amount=amount,
        currency=currency,
        date=tx_date,
        description=description,
        category=category,
        mcc=mcc,
        notes=notes,
        extra=extra or None,
        is_pending=bool(tx.get("hold")),
        cashback_amount=(tx.get("cashbackAmount") or 0) / 100.0,
    ))

    # cashback as separate positive transaction
    cashback = tx.get("cashbackAmount", 0)
    if cashback > 0:
        cb_id = f"monobank_cashback_{tx['id']}"
        if not session.exec(select(Transaction).where(Transaction.monobank_id == cb_id)).first():
            session.add(Transaction(
                account_id=account_id,
                monobank_id=cb_id,
                amount=cashback / 100.0,
                currency=currency,
                date=tx_date,
                description=f"Cashback: {description}",
                category="Cashback",
            ))
    return True


def run_sync() -> int:
    """Sync all Monobank accounts. Returns number of transactions imported."""
    with Session(engine) as session:
        run = SyncRun(status="running")
        session.add(run)
        session.commit()
        run_id = run.id

    total_imported = 0
    error_msg: str | None = None

    try:
        info = get_client_info()
        log.info("mono_client", name=info.get("name"))

        accounts = [a for a in info.get("accounts", []) if a.get("type") in SYNC_ACCOUNT_TYPES]

        now_ts = int(datetime.now(timezone.utc).timestamp())
        fetch_days = settings.monobank_fetch_days

        for i, acc in enumerate(accounts):
            if i > 0:
                log.info("rate_limit_sleep", seconds=RATE_LIMIT_SLEEP)
                time.sleep(RATE_LIMIT_SLEEP)

            currency = CURRENCY_MAP.get(acc.get("currencyCode", 980), "UAH")
            acc_type = acc.get("type", "unknown")
            name = f"Monobank {ACCOUNT_TYPE_NAMES.get(acc_type, acc_type)} {currency}"
            balance = (acc.get("balance") or 0) / 100.0

            with Session(engine) as session:
                account = _upsert_account(session, acc["id"], name, currency, acc_type, balance)
                session.commit()
                account_id = account.id

            end_ts = now_ts
            remaining = fetch_days
            chunks: list[tuple[int, int]] = []
            while remaining > 0:
                days = min(CHUNK_DAYS, remaining)
                start_ts = end_ts - days * 86400
                chunks.append((start_ts, end_ts))
                end_ts = start_ts
                remaining -= days

            for j, (start_ts, chunk_end_ts) in enumerate(chunks):
                if j > 0:
                    time.sleep(RATE_LIMIT_SLEEP)
                log.info("fetching_chunk", account=name, chunk=j + 1, total=len(chunks))
                try:
                    txs = get_statement(acc["id"], start_ts, chunk_end_ts)
                except httpx.HTTPStatusError as e:
                    log.error("statement_failed", error=str(e))
                    continue

                with Session(engine) as session:
                    for tx in txs:
                        if _import_transaction(session, account_id, tx):
                            total_imported += 1
                    session.commit()

        log.info("sync_complete", tx_imported=total_imported)

    except Exception as exc:
        error_msg = str(exc)
        log.exception("sync_failed", error=error_msg)

    with Session(engine) as session:
        run = session.get(SyncRun, run_id)
        if run:
            run.status = "failed" if error_msg else "completed"
            run.completed_at = datetime.utcnow()
            run.tx_imported = total_imported
            run.error = error_msg
            session.add(run)
            session.commit()

    return total_imported
