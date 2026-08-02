from __future__ import annotations

from datetime import date
from typing import Tuple


class InvalidMonthFormatError(ValueError):
    """Raised when a month string is not YYYY-MM."""


def month_bounds(month: str) -> Tuple[date, date]:
    """Return [start, end) dates for a YYYY-MM month string."""
    try:
        year_s, month_s = month.split("-")
        year, mon = int(year_s), int(month_s)
        if mon < 1 or mon > 12:
            raise ValueError("month out of range")
        start = date(year, mon, 1)
        end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
        return start, end
    except ValueError as exc:
        raise InvalidMonthFormatError("Invalid month format") from exc
