"""Unit tests for period date helpers in queries.py."""

import calendar
from datetime import date

from finance_api.domains.insights.queries import (
    _month_range,
    _months_ago,
    _period_dates,
)


class TestPeriodDates:
    def test_this_month_starts_on_first(self) -> None:
        start, end = _period_dates("this_month")
        assert start.day == 1
        assert start.month == end.month
        assert start.year == end.year
        assert end == date.today()

    def test_last_month_is_full_previous_month(self) -> None:
        start, end = _period_dates("last_month")
        assert start.day == 1
        assert end.month == start.month
        assert end.year == start.year
        _, last_day = calendar.monthrange(end.year, end.month)
        assert end.day == last_day

    def test_last_7d_span(self) -> None:
        start, end = _period_dates("last_7d")
        assert end == date.today()
        assert (end - start).days == 7

    def test_last_30d_span(self) -> None:
        start, end = _period_dates("last_30d")
        assert (end - start).days == 30

    def test_last_90d_span(self) -> None:
        start, end = _period_dates("last_90d")
        assert (end - start).days == 90

    def test_unknown_period_falls_back_to_this_month(self) -> None:
        start, end = _period_dates("bogus_value")
        this_start, this_end = _period_dates("this_month")
        assert start == this_start
        assert end == this_end

    def test_start_is_not_after_end(self) -> None:
        for period in ("this_month", "last_month", "last_7d", "last_30d", "last_90d"):
            start, end = _period_dates(period)
            assert start <= end, f"start > end for period={period}"


class TestMonthRange:
    def test_january(self) -> None:
        first, last = _month_range(2026, 1)
        assert first == date(2026, 1, 1)
        assert last == date(2026, 1, 31)

    def test_february_non_leap(self) -> None:
        first, last = _month_range(2025, 2)
        assert first == date(2025, 2, 1)
        assert last == date(2025, 2, 28)

    def test_february_leap(self) -> None:
        first, last = _month_range(2024, 2)
        assert first == date(2024, 2, 1)
        assert last == date(2024, 2, 29)

    def test_december_wraps_year(self) -> None:
        first, last = _month_range(2025, 12)
        assert first == date(2025, 12, 1)
        assert last == date(2025, 12, 31)

    def test_all_months_have_correct_first_day(self) -> None:
        for m in range(1, 13):
            first, _ = _month_range(2026, m)
            assert first.day == 1
            assert first.month == m


class TestMonthsAgo:
    def test_zero_is_current_month(self) -> None:
        year, month = _months_ago(0)
        today = date.today()
        assert year == today.year
        assert month == today.month

    def test_rolls_over_year_boundary(self) -> None:
        today = date.today()
        # Going back `today.month` months always lands in the previous year
        year, _month = _months_ago(today.month)
        assert year == today.year - 1

    def test_result_is_valid_month(self) -> None:
        for n in range(0, 25):
            year, month = _months_ago(n)
            assert 1 <= month <= 12
            assert year >= 2000
