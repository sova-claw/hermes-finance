"""LLM tool definitions — thin wrappers over queries.py for Claude tool use."""
from __future__ import annotations

from finance_api.domains.insights.charts import generate_chart
from finance_api.domains.insights.queries import (
    get_account_balances,
    get_monthly_trend,
    get_recent_transactions,
    get_spending_by_category,
)

# JSON Schema tool definitions for Claude
TOOLS: list[dict] = [
    {
        "name": "get_account_balances",
        "description": "Return current balances for all Monobank accounts.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_spending_by_category",
        "description": (
            "Return spending totals grouped by category for a period. "
            "Periods: this_month, last_month, last_7d, last_30d, last_90d."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": [
                        "this_month", "last_month", "last_7d",
                        "last_30d", "last_90d",
                    ],
                    "description": "Time window. Default: this_month.",
                },
            },
        },
    },
    {
        "name": "get_monthly_trend",
        "description": "Return month-by-month income and expense totals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "months": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 24,
                    "description": "Number of calendar months. Default: 3.",
                },
            },
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Return the most recent transactions (newest first).",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "How many transactions. Default: 20.",
                },
            },
        },
    },
    {
        "name": "generate_chart",
        "description": (
            "Render a chart PNG and return its file type. "
            "Types: spending_pie (pie chart of categories this month), "
            "monthly_bar (income vs expenses bar chart for last 3 months)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["spending_pie", "monthly_bar"],
                    "description": "Which chart to render.",
                },
            },
            "required": ["chart_type"],
        },
    },
]


def dispatch(name: str, **kwargs) -> dict | list | str:
    """Dispatch a tool call by name. Returns JSON-serializable data or a chart path.

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
