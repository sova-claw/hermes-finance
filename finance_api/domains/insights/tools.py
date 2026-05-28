"""Tool dispatch — thin wrappers over queries.py."""
from __future__ import annotations

from finance_api.domains.insights.charts import generate_chart
from finance_api.domains.insights.queries import (
    get_account_balances,
    get_monthly_trend,
    get_recent_transactions,
    get_spending_by_category,
)


def dispatch(name: str, **kwargs) -> dict | list | str:
    """Dispatch a tool call by name.

    Returns:
        Tool-specific data (dict, list) or a file path string for charts.
    """
    match name:
        case "get_account_balances":
            return get_account_balances()
        case "get_spending_by_category":
            return get_spending_by_category(kwargs.get("period", "this_month"))
        case "get_monthly_trend":
            return get_monthly_trend(kwargs.get("months", 3))
        case "get_recent_transactions":
            return get_recent_transactions(kwargs.get("limit", 20))
        case "generate_chart":
            chart_type = kwargs["chart_type"]
            data = (
                get_spending_by_category("this_month")
                if chart_type == "spending_pie"
                else get_monthly_trend(3)
            )
            return generate_chart(chart_type, data)
        case _:
            raise ValueError(f"Unknown tool: {name}")
