"""Claude tool definitions and dispatcher for financial analytics."""
from typing import Any

from finance_api.domains.insights import queries, charts

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_account_balances",
        "description": "Returns current balances for all connected bank accounts.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_spending_by_category",
        "description": "Returns total spending grouped by category for a given period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["this_month", "last_month", "last_7d", "last_30d", "last_90d"],
                    "description": "Time period to analyze",
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_monthly_trend",
        "description": "Returns month-by-month income and expense totals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "months": {
                    "type": "integer",
                    "description": "Number of months to include (default 3)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Returns the most recent transactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max number of transactions (default 20)"}
            },
            "required": [],
        },
    },
    {
        "name": "generate_chart",
        "description": "Generates a chart image and returns the file path. Use this when the user asks for a visual breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["pie_by_category", "monthly_bar", "income_vs_expense"],
                },
                "period": {
                    "type": "string",
                    "enum": ["this_month", "last_month", "last_7d", "last_30d", "last_90d"],
                    "description": "Period for pie_by_category chart",
                },
                "months": {
                    "type": "integer",
                    "description": "Months for monthly_bar / income_vs_expense chart",
                },
            },
            "required": ["chart_type"],
        },
    },
]


def dispatch(tool_name: str, tool_input: dict[str, Any]) -> Any:
    if tool_name == "get_account_balances":
        return queries.get_account_balances()

    if tool_name == "get_spending_by_category":
        return queries.get_spending_by_category(tool_input.get("period", "this_month"))

    if tool_name == "get_monthly_trend":
        return queries.get_monthly_trend(tool_input.get("months", 3))

    if tool_name == "get_recent_transactions":
        return queries.get_recent_transactions(tool_input.get("limit", 20))

    if tool_name == "generate_chart":
        chart_type = tool_input["chart_type"]
        if chart_type == "pie_by_category":
            data = queries.get_spending_by_category(tool_input.get("period", "this_month"))
            return {"file_path": charts.pie_by_category(data)}
        if chart_type in ("monthly_bar", "income_vs_expense"):
            data = queries.get_monthly_trend(tool_input.get("months", 3))
            fn = charts.monthly_bar if chart_type == "monthly_bar" else charts.income_vs_expense
            return {"file_path": fn(data)}

    raise ValueError(f"Unknown tool: {tool_name}")
