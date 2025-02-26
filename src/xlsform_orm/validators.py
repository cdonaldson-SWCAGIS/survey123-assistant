"""Validators for XLSForm ORM."""

import re
from typing import Optional, Tuple

from .constants import RESERVED_NAMES


def validate_name(name: str) -> str:
    """Validate a name field."""
    if not name:
        raise ValueError("Name cannot be empty")

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            "Name must start with a letter or underscore and contain only letters, numbers, and underscores"
        )

    if name.upper() in RESERVED_NAMES:
        raise ValueError(f"Name '{name}' is a reserved word")

    return name


def check_appearance_attributes(appearance: Optional[str]) -> Optional[str]:
    """Check appearance attributes."""
    if appearance is None:
        return None

    if appearance.startswith("w"):
        try:
            parse_grid_theme_appearance(appearance)
        except ValueError as e:
            raise ValueError(f"Invalid grid theme format: {e}")

    return appearance


def parse_grid_theme_appearance(appearance: str) -> Tuple[int, int]:
    """Parse grid theme appearance parameter.

    Args:
        appearance: The appearance parameter string (e.g., "w4" or "w3:2")

    Returns:
        Tuple of (columns, span)

    Raises:
        ValueError: If the appearance parameter is invalid
    """
    if not appearance.startswith("w"):
        raise ValueError("Grid theme must start with 'w'")

    parts = appearance[1:].split(":")
    if len(parts) > 2 or not parts[0]:
        raise ValueError("Invalid grid theme format")

    try:
        columns = int(parts[0])
        span = int(parts[1]) if len(parts) > 1 else 1
    except ValueError:
        raise ValueError("Invalid grid theme format")

    if columns <= 0:
        raise ValueError("Number of columns must be positive")
    if span <= 0:
        raise ValueError("Span must be positive")

    return columns, span


def validate_grid_theme_for_group(
    columns: int, span: int, parent_columns: Optional[int] = None
) -> bool:
    """Validate grid theme parameters for a group.

    Args:
        columns: Number of columns in this group's grid
        span: Number of parent columns this group spans
        parent_columns: Number of columns in parent grid (if any)

    Returns:
        True if valid

    Raises:
        ValueError: If parameters are invalid
    """
    if parent_columns is not None and span > parent_columns:
        raise ValueError(
            f"Group span {span} exceeds available columns {parent_columns}"
        )

    return True
