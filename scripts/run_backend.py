#!/usr/bin/env python
"""Run the local API server with a configurable, project-specific port."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn


DEFAULT_API_PORT = 5511
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _environment_port() -> int:
    raw_port = os.getenv("WHO_MESSED_UP_API_PORT", str(DEFAULT_API_PORT))
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("WHO_MESSED_UP_API_PORT must be an integer.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("WHO_MESSED_UP_API_PORT must be between 1 and 65535.")
    return port


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Who Messed Up API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=_environment_port())
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(PROJECT_ROOT))
    uvicorn.run("app:app", host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
