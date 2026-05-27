"""Chart generation via matplotlib — returns PNG file path."""
import io
import tempfile
from typing import Any

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt


def _save_fig(fig: Any) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return tmp.name


def pie_by_category(data: dict[str, float], title: str = "Spending by Category") -> str:
    if not data:
        raise ValueError("No data to chart")
    labels = list(data.keys())
    values = list(data.values())
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    ax.set_title(title)
    return _save_fig(fig)


def monthly_bar(data: list[dict[str, Any]], title: str = "Monthly Trend") -> str:
    if not data:
        raise ValueError("No data to chart")
    months = [d["month"] for d in data]
    incomes = [d["income"] for d in data]
    expenses = [d["expenses"] for d in data]

    x = range(len(months))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - width / 2 for i in x], incomes, width, label="Income", color="#22c55e")
    ax.bar([i + width / 2 for i in x], expenses, width, label="Expenses", color="#ef4444")
    ax.set_xticks(list(x))
    ax.set_xticklabels(months)
    ax.set_title(title)
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return _save_fig(fig)


def income_vs_expense(data: list[dict[str, Any]], title: str = "Income vs Expenses") -> str:
    return monthly_bar(data, title)
