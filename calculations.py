from calendar import monthrange
from datetime import date

def month_key(dt: date) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"

def pro_rata(B_total: int, today: date) -> dict:
    D = monthrange(today.year, today.month)[1]
    d = today.day
    R = max(0, D - d)
    target = B_total * d / D
    return {"D": D, "d": d, "R": R, "target": target}

def daily_cap(B_total: int, spent: int, today: date) -> int:
    D = monthrange(today.year, today.month)[1]
    R = max(0, D - today.day)
    rem = max(0, B_total - spent)
    return int(rem / R) if R else 0
