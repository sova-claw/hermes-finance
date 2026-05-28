"""Budget CRUD and vs-spending analytics."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from finance_api.core.db.engine import engine
from finance_api.domains.budgets.models import CategoryBudget
from finance_api.domains.insights.queries import get_spending_by_category
from finance_api.schemas import BudgetItem, BudgetSet


def list_budgets_vs_spending() -> list[BudgetItem]:
    """Return all budget limits annotated with current-month spending."""
    spending = get_spending_by_category(period="this_month")
    with Session(engine) as session:
        budgets = session.exec(select(CategoryBudget)).all()
    result = []
    for b in budgets:
        spent = spending.get(b.category, 0.0)
        remaining = b.monthly_limit - spent
        result.append(
            BudgetItem(
                category=b.category,
                monthly_limit=b.monthly_limit,
                currency=b.currency,
                spent=round(spent, 2),
                remaining=round(remaining, 2),
                exceeded=spent > b.monthly_limit,
            )
        )
    return sorted(result, key=lambda r: r.exceeded, reverse=True)


def upsert_budget(
    category: str,
    monthly_limit: float,
    currency: str = "UAH",
) -> BudgetSet:
    """Create or update a monthly limit for a category."""
    with Session(engine) as session:
        existing = session.exec(
            select(CategoryBudget).where(CategoryBudget.category == category)
        ).first()
        if existing:
            existing.monthly_limit = monthly_limit
            existing.currency = currency
            existing.updated_at = datetime.now(UTC)
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return BudgetSet(
                category=existing.category,
                monthly_limit=existing.monthly_limit,
                currency=existing.currency,
            )
        budget = CategoryBudget(
            category=category,
            monthly_limit=monthly_limit,
            currency=currency,
        )
        session.add(budget)
        session.commit()
        session.refresh(budget)
        return BudgetSet(
            category=budget.category,
            monthly_limit=budget.monthly_limit,
            currency=budget.currency,
        )


def delete_budget(category: str) -> bool:
    """Remove a budget limit. Returns True if it existed."""
    with Session(engine) as session:
        existing = session.exec(
            select(CategoryBudget).where(CategoryBudget.category == category)
        ).first()
        if not existing:
            return False
        session.delete(existing)
        session.commit()
        return True
