"""
Helpers for loading environment variables from a .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv as _load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _load_dotenv = None  # type: ignore

_ENV_LOADED = False


def load_env(dotenv_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file if python-dotenv is installed.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    if _load_dotenv is None:
        _ENV_LOADED = True
        return

    path = dotenv_path or Path(os.getcwd()) / ".env"
    _load_dotenv(dotenv_path=path, override=False)
    _ENV_LOADED = True
