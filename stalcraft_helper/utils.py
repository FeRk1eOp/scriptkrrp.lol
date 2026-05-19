"""Shared helpers: number formatting, paths, persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def app_data_dir() -> Path:
    """Return per-user directory for app state and copied images."""
    base = os.environ.get("STALCRAFT_HELPER_HOME")
    if base:
        path = Path(base)
    else:
        path = Path.home() / ".stalcraft_helper"
    path.mkdir(parents=True, exist_ok=True)
    (path / "images").mkdir(parents=True, exist_ok=True)
    return path


def state_file() -> Path:
    return app_data_dir() / "state.json"


def load_state() -> dict[str, Any]:
    path = state_file()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
        return {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(data: dict[str, Any]) -> None:
    path = state_file()
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


def format_number(value: float, decimals: int = 0) -> str:
    """Format a number with thin-space thousand separators (RU style)."""
    if decimals <= 0:
        rounded = int(round(value))
        s = f"{rounded:,}".replace(",", " ")
        return s
    rounded = round(value, decimals)
    whole, _, frac = f"{rounded:,.{decimals}f}".partition(".")
    whole = whole.replace(",", " ")
    if frac:
        return f"{whole},{frac}"
    return whole
