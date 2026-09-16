#!/usr/bin/env python3
"""Fetch latest quotes from Render live-quotes gateway and write data/stock_data.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

from fetch_shioaji_data import (
    STOCKS_META,
    compute_institutional_analysis,
    fetch_twse_institutional_flow,
)
from fundamental_data import fetch_fundamental_snapshot

LIVE_QUOTES_URL = "https://futienchun-com-dashboard.onrender.com/api/live-quotes"
TIMEOUT_SECONDS = 180
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "stock_data.json"
CACHE_VERSION = "20260916-quote-flow-sync-r3"


def live_quote_payload_error(payload: object) -> str | None:
    """Reject incomplete live data instead of advancing its freshness metadata."""
    if not isinstance(payload, dict):
        return "live-quotes returned a non-object payload"

    stocks = payload.get("stocks")
    if not isinstance(stocks, list):
        return "live-quotes returned no stock list"

    expected_codes = set(STOCKS_META)
    by_code = {
        str(stock.get("code")): stock
        for stock in stocks
        if isinstance(stock, dict) and stock.get("code")
    }
    missing_codes = sorted(expected_codes - set(by_code))
    if missing_codes:
        return "live-quotes is missing stocks: " + ", ".join(missing_codes)

    invalid_codes = [
        code
        for code in sorted(expected_codes)
        if not isinstance(by_code[code].get("last_price"), (int, float))
        or by_code[code]["last_price"] <= 0
    ]
    if invalid_codes:
        return "live-quotes has invalid prices: " + ", ".join(invalid_codes)

    quote_status = payload.get("quote_status")
    if not isinstance(quote_status, dict) or quote_status.get("status") != "ok":
        return "live-quotes did not confirm a complete quote refresh"

    if not payload.get("quote_updated_at") or not payload.get("market_as_of"):
        return "live-quotes is missing quote freshness metadata"

    return None


def main() -> int:
    previous_payload = {}
    try:
        previous_payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        previous_payload = {}

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

    payload_error = live_quote_payload_error(payload)
    if payload_error:
        print(f"ERROR: {payload_error}", file=sys.stderr)
        return 1
    stocks = payload["stocks"]

    previous_stocks = {
        str(stock.get("code")): stock
        for stock in previous_payload.get("stocks", [])
        if isinstance(stock, dict) and stock.get("code")
    }
    institutional_data, institutional_status = fetch_twse_institutional_flow(
        list(STOCKS_META)
    )
    institutional_refresh_ok = (
        institutional_status.get("status") == "ok"
        and set(STOCKS_META).issubset(institutional_data)
    )
    fundamental_updates, fundamental_status = fetch_fundamental_snapshot(STOCKS_META)
    for stock in stocks:
        code = str(stock.get("code", ""))
        previous_stock = previous_stocks.get(code, {})
        if institutional_refresh_ok and code in STOCKS_META:
            institutional_flow, capital_inflow = compute_institutional_analysis(
                code,
                STOCKS_META[code]["name"],
                institutional_data,
                stock.get("volume"),
            )
            stock["institutional_flow"] = institutional_flow
            stock["capital_inflow"] = capital_inflow
        else:
            current_flow = stock.get("institutional_flow") or {}
            previous_flow = previous_stock.get("institutional_flow")
            previous_capital = previous_stock.get("capital_inflow")
            if (
                current_flow.get("date") in (None, "-")
                and isinstance(previous_flow, dict)
                and previous_flow.get("date") not in (None, "-")
            ):
                stock["institutional_flow"] = previous_flow
            if (
                current_flow.get("date") in (None, "-")
                and isinstance(previous_capital, dict)
                and previous_capital.get("capital_status")
                not in (None, "暂无法人筹码动向")
            ):
                stock["capital_inflow"] = previous_capital
        update = fundamental_updates.get(code, {})
        for field in (
            "gross_margin",
            "net_margin",
            "roe",
            "eps_single",
            "earnings_date",
            "event_status",
            "event_checked_at",
            "fundamental_as_of",
            "latest_monthly_revenue",
            "latest_quarter",
        ):
            if update.get(field) is not None:
                stock[field] = update[field]

        latest_quarter = update.get("latest_quarter")
        if latest_quarter:
            rows = [
                row
                for row in stock.get("quarterly_earnings", [])
                if row.get("period") != latest_quarter.get("period")
            ]
            stock["quarterly_earnings"] = (rows + [latest_quarter])[-4:]

        links = list(stock.get("source_links") or [])
        known_urls = {item.get("url") for item in links}
        for source in update.get("official_source_links", []):
            if source.get("url") not in known_urls:
                links.append(source)
        stock["source_links"] = links

    now_str = payload["quote_updated_at"]
    payload["updated_at"] = now_str
    payload["cache_version"] = CACHE_VERSION
    if fundamental_status.get("status") == "ok":
        payload["fundamental_updated_at"] = fundamental_status.get("updated_at")
        payload["fundamental_as_of"] = fundamental_status.get("as_of")
    else:
        payload["fundamental_updated_at"] = (
            previous_payload.get("fundamental_updated_at")
            or fundamental_status.get("updated_at")
        )
        payload["fundamental_as_of"] = (
            fundamental_status.get("as_of")
            or previous_payload.get("fundamental_as_of")
        )
    payload["fundamental_checked_at"] = fundamental_status.get("updated_at")
    payload["fundamental_source"] = fundamental_status.get("source")
    payload["fundamental_status"] = fundamental_status
    if institutional_refresh_ok:
        payload["institutional_as_of"] = institutional_status["date"]
    else:
        payload["institutional_as_of"] = (
            payload.get("institutional_as_of")
            or previous_payload.get("institutional_as_of")
        )
    payload["institutional_status"] = {
        **institutional_status,
        "flow_count": len(institutional_data),
        "as_of": institutional_status.get("date")
        if institutional_refresh_ok
        else payload["institutional_as_of"],
    }
    sources = payload.get("sources")
    payload["sources"] = sources if isinstance(sources, dict) else {}
    payload["sources"]["twse_t86_flow"] = payload["institutional_status"]
    payload["research_updated_at"] = payload.get("weekly_review", {}).get("as_of")

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
