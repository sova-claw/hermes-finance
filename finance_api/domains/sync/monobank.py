"""Monobank → PostgreSQL transaction sync."""

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlmodel import Session, select

from finance_api.core.config import settings
from finance_api.core.db.engine import engine
from finance_api.domains.accounts.models import Account
from finance_api.domains.sync.client import MonobankClient
from finance_api.domains.sync.mcc import MCC_LOOKUP
from finance_api.domains.sync.models import SyncRun
from finance_api.domains.transactions import categories as cat
from finance_api.domains.transactions.models import Transaction

log = structlog.get_logger(__name__)

# Process-local lock — safe because gunicorn runs workers=1
_sync_lock = threading.Lock()

CHUNK_DAYS = 31
OVERLAP_HOURS = 24

CURRENCY_MAP = {
    980: "UAH",
    840: "USD",
    978: "EUR",
    826: "GBP",
    756: "CHF",
    985: "PLN",
    203: "CZK",
}

SYNC_ACCOUNT_TYPES = {"black", "white", "fop", "platinum", "iron", "yellow"}

ACCOUNT_TYPE_NAMES = {
    "black": "Black",
    "white": "White",
    "fop": "FOP",
    "iron": "Iron",
    "platinum": "Platinum",
    "yellow": "Yellow",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _get_or_create_account(
    session: Session,
    mono_id: str,
    name: str,
    currency: str,
    account_type: str,
    balance: float,
) -> Account:
    """Get existing account or create new one with the given parameters."""
    existing = session.exec(
        select(Account).where(Account.monobank_id == mono_id)
    ).first()
    if existing:
        existing.balance = balance
        session.add(existing)
        return existing
    account = Account(
        monobank_id=mono_id,
        name=name,
        currency=currency,
        account_type=account_type,
        balance=balance,
    )
    session.add(account)
    session.flush()
    return account


def _parse_tx(
    tx: dict[str, Any], account_id: uuid.UUID, currency: str
) -> Transaction | None:
    """Build a Transaction from Monobank API dict; None if amount is zero."""
    amount_minor = tx.get("amount", 0)
    if amount_minor == 0:
        return None

    monobank_id = f"monobank_{tx['id']}"
    amount = amount_minor / 100.0
    tx_currency = CURRENCY_MAP.get(tx.get("currencyCode", 980), currency)
    tx_date = datetime.fromtimestamp(tx["time"], tz=UTC).date()
    description = tx.get("description") or "Monobank"
    notes = tx.get("comment") or None
    mcc = int(tx["mcc"]) if tx.get("mcc") else None
    category = MCC_LOOKUP.get(mcc) if mcc else None

    extra: dict[str, Any] = {}
    if tx.get("hold"):
        extra["pending"] = True
    op_amount = tx.get("operationAmount")
    if op_amount and abs(op_amount) > 0 and abs(op_amount) != abs(amount_minor):
        extra["exchange_rate"] = round(abs(amount_minor) / abs(op_amount), 6)

    return Transaction(
        account_id=account_id,
        monobank_id=monobank_id,
        amount=amount,
        currency=tx_currency,
        date=tx_date,
        description=description,
        category=category,
        mcc=mcc,
        notes=notes,
        extra=extra or None,
        is_pending=bool(tx.get("hold")),
        cashback_amount=(tx.get("cashbackAmount") or 0) / 100.0,
    )


def _parse_cashback(
    tx: dict[str, Any], account_id: uuid.UUID, currency: str
) -> Transaction | None:
    """Build a cashback Transaction if Monobank tx has cashbackAmount > 0."""
    cashback = tx.get("cashbackAmount", 0)
    if cashback <= 0:
        return None
    tx_currency = CURRENCY_MAP.get(tx.get("currencyCode", 980), currency)
    tx_date = datetime.fromtimestamp(tx["time"], tz=UTC).date()
    description = tx.get("description") or "Monobank"
    return Transaction(
        account_id=account_id,
        monobank_id=f"monobank_cashback_{tx['id']}",
        amount=cashback / 100.0,
        currency=tx_currency,
        date=tx_date,
        description=f"Cashback: {description}",
        category=cat.CASHBACK,
    )


def _build_chunks(from_ts: int, to_ts: int) -> list[tuple[int, int]]:
    """Split [from_ts, to_ts] into CHUNK_DAYS-day windows."""
    chunks: list[tuple[int, int]] = []
    end = to_ts
    while end > from_ts:
        start = max(end - CHUNK_DAYS * 86400, from_ts)
        chunks.append((start, end))
        end = start
    return chunks


def _sync_account(client: MonobankClient, acc: dict[str, Any], now_ts: int) -> int:
    """Sync one account. Returns number of new transactions imported."""
    mono_id = acc["id"]
    currency = CURRENCY_MAP.get(acc.get("currencyCode", 980), "UAH")
    acc_type = acc.get("type", "unknown")
    name = f"Monobank {ACCOUNT_TYPE_NAMES.get(acc_type, acc_type)} {currency}"
    balance = (acc.get("balance") or 0) / 100.0

    with Session(engine) as session:
        account = _get_or_create_account(
            session, mono_id, name, currency, acc_type, balance
        )
        session.commit()
        account_id = account.id
        last_synced = account.synced_at

    fetch_from = now_ts - settings.monobank_fetch_days * 86400
    if last_synced:
        # overlap by OVERLAP_HOURS to catch late-arriving transactions
        overlap_ts = int(last_synced.timestamp()) - OVERLAP_HOURS * 3600
        fetch_from = max(fetch_from, overlap_ts)

    chunks = _build_chunks(fetch_from, now_ts)
    imported = 0

    for i, (start_ts, chunk_end_ts) in enumerate(chunks):
        log.info("fetching_chunk", account=name, chunk=i + 1, total=len(chunks))
        try:
            txs = client.get_statement(mono_id, start_ts, chunk_end_ts)
        except Exception as exc:
            log.error("statement_failed", account=name, error=str(exc))
            continue

        monobank_ids = [f"monobank_{tx['id']}" for tx in txs]
        cashback_ids = [
            f"monobank_cashback_{tx['id']}"
            for tx in txs
            if tx.get("cashbackAmount", 0) > 0
        ]

        with Session(engine) as session:
            existing_ids: set[str] = set(
                session.exec(
                    select(Transaction.monobank_id).where(
                        Transaction.monobank_id.in_(monobank_ids + cashback_ids)  # type: ignore[attr-defined]
                    )
                ).all()
            )

            for tx in txs:
                parsed = _parse_tx(tx, account_id, currency)
                if parsed and parsed.monobank_id not in existing_ids:
                    session.add(parsed)
                    imported += 1

                cb = _parse_cashback(tx, account_id, currency)
                if cb and cb.monobank_id not in existing_ids:
                    session.add(cb)
                    imported += 1

            session.commit()

    # Mark account synced_at only after all chunks complete
    with Session(engine) as session:
        updated_account: Account | None = session.exec(
            select(Account).where(Account.monobank_id == mono_id)
        ).first()
        if updated_account:
            updated_account.synced_at = _now()
            session.add(updated_account)
            session.commit()

    return imported


def run_sync() -> int:
    """Sync all Monobank accounts. Returns number of transactions imported."""
    if not _sync_lock.acquire(blocking=False):
        log.info("sync_skipped", reason="already_running")
        return 0

    with Session(engine) as session:
        run = SyncRun(status="running")
        session.add(run)
        session.commit()
        run_id = run.id

    total_imported = 0
    error_msg: str | None = None

    try:
        with MonobankClient(token=settings.monobank_token) as client:
            info = client.get_client_info()
            log.info("mono_client", name=info.get("name"))

            accounts = [
                a
                for a in info.get("accounts", [])
                if a.get("type") in SYNC_ACCOUNT_TYPES
            ]
            now_ts = int(_now().timestamp())

            for acc in accounts:
                imported = _sync_account(client, acc, now_ts)
                total_imported += imported
                log.info("account_synced", account_id=acc["id"], imported=imported)

        log.info("sync_complete", tx_imported=total_imported)

    except Exception as exc:
        error_msg = str(exc)
        log.exception("sync_failed", error=error_msg)

    finally:
        _sync_lock.release()

    with Session(engine) as session:
        sync_run: SyncRun | None = session.get(SyncRun, run_id)
        if sync_run:
            sync_run.status = "failed" if error_msg else "completed"
            sync_run.completed_at = _now()
            sync_run.tx_imported = total_imported
            sync_run.error = error_msg
            session.add(sync_run)
            session.commit()

    return total_imported
