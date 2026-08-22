#!/usr/bin/env python3
"""Fetch latest quotes from Render live-quotes gateway and write data/stock_data.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

LIVE_QUOTES_URL = "https://futienchun-com-dashboard.onrender.com/api/live-quotes"
TIMEOUT_SECONDS = 180
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "stock_data.json"


def main() -> int:
    try:
        response = requests.post(
            LIVE_QUOTES_URL,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        print(f"ERROR: live-quotes request failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        body = (response.text or "")[:500]
        print(
            f"ERROR: live-quotes HTTP {response.status_code}; body={body!r}",
            file=sys.stderr,
        )
        return 1

    try:
        payload = response.json()
    except ValueError as exc:
        print(f"ERROR: live-quotes JSON decode failed: {exc}", file=sys.stderr)
        return 1

    stocks = payload.get("stocks") if isinstance(payload, dict) else None
    if not isinstance(stocks, list) or len(stocks) == 0:
        print("ERROR: live-quotes returned empty stocks", file=sys.stderr)
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        "OK wrote",
        OUTPUT_PATH,
        "stocks=",
        len(stocks),
        "updated_at=",
        payload.get("updated_at"),
        "data_source=",
        payload.get("data_source"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
