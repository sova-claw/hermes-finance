"""Chart generation — takes data, returns PNG path."""
from __future__ import annotations

import os
import tempfile
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_IMPORT_ERROR: str | None = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
except ImportError as exc:
    _IMPORT_ERROR = str(exc)
    log.warning("matplotlib_not_available", error=str(exc))


def _out_path(name: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"finance_chart_{name}.png")


def generate_chart(chart_type: str, data: dict | list) -> str:
    """Render a chart and return its temporary file path.

    Returns:
        Path to the generated PNG file.
    """
    if _IMPORT_ERROR:
        return f"Chart unavailable: {_IMPORT_ERROR}"

    match chart_type:
        case "spending_pie":
            return _spending_pie(data)
        case "monthly_bar":
            return _monthly_bar(data)
        case _:
            return f"Unknown chart type: {chart_type}"


def _spending_pie(data: dict | list) -> str:
    """Pie chart of spending by category.

    Returns:
        Path to the generated PNG file.
    """
    categories = data if isinstance(data, dict) else {}
    if not categories:
        categories = {"No data": 1}

    labels = sorted(
        categories.keys(), key=lambda k: categories[k], reverse=True
    )
    values = [categories[lb] for lb in labels]

    fig, ax = plt.subplots(figsize=(8, 6))
    colours = plt.cm.Set3(range(len(labels)))
    _, _, autotexts = ax.pie(
        values, labels=labels, autopct="%1.0f%%",
        colors=colours, pctdistance=0.85,
    )
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title("Spending by Category", fontsize=14, pad=20)

    path = _out_path("spending")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _monthly_bar(data: dict | list) -> str:
    """Grouped bar chart: income vs expenses per month.

    Returns:
        Path to the generated PNG file.
    """
    rows: list[dict[str, Any]] = data if isinstance(data, list) else []
    if not rows:
        rows = [{"month": "No data", "income": 0, "expenses": 0}]

    months = [r["month"] for r in rows]
    income = [r["income"] for r in rows]
    expenses = [r["expenses"] for r in rows]

    x = range(len(months))
    w = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    colour_income = "#2ecc71"
    colour_expense = "#e74c3c"
    ax.bar(
        [i - w / 2 for i in x], income, w,
        label="Income", colour=colour_income, alpha=0.85,
    )
    ax.bar(
        [i + w / 2 for i in x], expenses, w,
        label="Expenses", colour=colour_expense, alpha=0.85,
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=30, ha="right")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:,.0f}")
    )
    ax.set_title("Monthly Income vs Expenses", fontsize=14)
    ax.legend()
    fig.tight_layout()

    path = _out_path("trend")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
