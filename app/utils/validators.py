"""
Validation Utilities
"""
import re


HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")

VALID_ACCOUNT_TYPES = ("debit", "credit", "investment")
VALID_DIRECTIONS = ("in", "out")
VALID_GROUP_TYPES = ("expense", "income")


def validate_account_type(account_type: str) -> bool:
    """Validate account type is one of the allowed values."""
    return account_type in VALID_ACCOUNT_TYPES


def validate_direction(direction: str) -> bool:
    """Validate transaction direction is valid."""
    return direction in VALID_DIRECTIONS


def validate_group_type(group_type: str) -> bool:
    """Validate category group type is valid."""
    return group_type in VALID_GROUP_TYPES


def validate_hex_color(color: str) -> bool:
    """Validate hex color format (#RRGGBB)."""
    return bool(HEX_COLOR_REGEX.match(color))


def parse_float(value: str, default: float = 0.0) -> float:
    """Safely parse a float from string input."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_int(value: str, default: int = 0) -> int:
    """Safely parse an integer from string input."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def dollars_to_cents(dollars: float) -> int:
    """Convert dollar amount to cents (integer)."""
    return int(round(dollars * 100))


def cents_to_dollars(cents: int) -> float:
    """Convert cents to dollar amount."""
    return cents / 100
