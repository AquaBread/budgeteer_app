"""
Date Helper Utilities
"""
from datetime import date


def month_key(dt: date) -> str:
    """Convert a date to YYYY-MM format."""
    return f"{dt.year:04d}-{dt.month:02d}"


def add_months(y: int, m: int, delta: int) -> tuple:
    """Add delta months to a year/month pair."""
    m2 = m + delta
    y2 = y + (m2 - 1) // 12
    m2 = (m2 - 1) % 12 + 1
    return y2, m2


def month_key_from_ym(y: int, m: int) -> str:
    """Convert year and month to YYYY-MM format."""
    return f"{y:04d}-{m:02d}"


def prev_month_key(mkey: str) -> str:
    """
    Given 'YYYY-MM' return the previous month.
    """
    year, mon = map(int, mkey.split('-'))
    if mon == 1:
        return f"{year - 1:04d}-12"
    else:
        return f"{year:04d}-{mon - 1:02d}"


def month_seq(start_mkey: str, end_mkey: str) -> list:
    """
    Inclusive list of YYYY-MM between start and end.
    """
    y1, m1 = map(int, start_mkey.split("-"))
    y2, m2 = map(int, end_mkey.split("-"))

    out = []
    y, m = y1, m1
    while (y < y2) or (y == y2 and m <= m2):
        out.append(f"{y:04d}-{m:02d}")
        y, m = add_months(y, m, 1)

    return out
