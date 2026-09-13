#!/usr/bin/env python3
"""Fetch official TWSE fundamental snapshots used by the dashboard."""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.request
from typing import Any, Iterable


TWSE_OPENAPI_BASE = "https://openapi.twse.com.tw/v1/opendata"
MOPS_CONFERENCE_URL = "https://mops.twse.com.tw/mops/web/t100sb02_1"
FUNDAMENTAL_ENDPOINTS = {
    "monthly_revenue": "t187ap05_L",
    "operating_analysis": "t187ap17_L",
    "income_statement": "t187ap06_L_ci",
    "balance_sheet": "t187ap07_L_ci",
}


def _fetch_json(endpoint: str) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                f"{TWSE_OPENAPI_BASE}/{endpoint}",
                headers={
                    "User-Agent": "TaiwanStockDashboard/1.0",
                    "Accept": "application/json",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError(f"TWSE OpenAPI {endpoint} returned a non-list payload")
            return [row for row in payload if isinstance(row, dict)]
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError(f"TWSE OpenAPI {endpoint} failed")


def _code(row: dict[str, Any]) -> str:
    return str(row.get("公司代號", "")).strip()


def _number(value: Any) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _format_percent(value: Any, suffix: str = "%") -> str | None:
    numeric = _number(value)
    return f"{numeric:.2f}{suffix}" if numeric is not None else None


def _format_signed_percent(value: Any) -> str | None:
    numeric = _number(value)
    return f"{numeric:+.2f}%" if numeric is not None else None


def _format_million_from_thousand(value: Any) -> str | None:
    numeric = _number(value)
    if numeric is None:
        return None
    return f"{numeric / 1000:,.0f} 百萬元"


def _roc_date(value: Any) -> str | None:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    if len(digits) != 7:
        return None
    try:
        year = int(digits[:3]) + 1911
        parsed = dt.date(year, int(digits[3:5]), int(digits[5:7]))
    except ValueError:
        return None
    return parsed.isoformat()


def _period(row: dict[str, Any]) -> str | None:
    year = _number(row.get("年度"))
    quarter = str(row.get("季別", "")).strip()
    if year is None or not quarter:
        return None
    return f"{int(year) + 1911}Q{quarter}"


def _latest_by_code(rows: Iterable[dict[str, Any]], codes: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = _code(row)
        if code in codes:
            result[code] = row
    return result


def _refresh_event_label(existing: str | None, today: dt.date) -> tuple[str, str]:
    """Make historical hard-coded event text explicit instead of leaving stale wording."""
    text = str(existing or "").strip()
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text)
    monthly_note = ""
    if "|" in text:
        monthly_note = " | " + text.split("|", 1)[1].strip()

    if match:
        event_date = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if event_date < today:
            period_match = re.search(r"(\d{2}Q\d)", text)
            period = period_match.group(1) if period_match else "前次"
            event_kind = "法說會" if "法說" in text or "法说" in text else "財報"
            return (
                f"{event_date.isoformat()} ({period} {event_kind}已舉行)"
                f"；下一次財報/法說會日期待公司公告{monthly_note}",
                "historical",
            )
        return (text.replace("本週五", "已排程").replace("本周五", "已排程"), "scheduled")

    return (text or "最新季度已公告；下一次財報/法說會日期待公司公告", "unknown")


def _official_links() -> list[dict[str, str]]:
    return [
        {"label": "TWSE OpenAPI 月營收", "url": f"{TWSE_OPENAPI_BASE}/{FUNDAMENTAL_ENDPOINTS['monthly_revenue']}"},
        {"label": "TWSE OpenAPI 季度營益分析", "url": f"{TWSE_OPENAPI_BASE}/{FUNDAMENTAL_ENDPOINTS['operating_analysis']}"},
        {"label": "MOPS 法說會一覽表", "url": MOPS_CONFERENCE_URL},
    ]


def fetch_fundamental_snapshot(
    stocks_meta: dict[str, dict[str, Any]],
    now: dt.datetime | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Return per-stock official facts and fetch status without destroying old values on failure."""
    current = now or dt.datetime.now()
    codes = set(stocks_meta)
    rows_by_source: dict[str, dict[str, dict[str, Any]]] = {}
    source_status: dict[str, dict[str, Any]] = {}
    as_of_dates: list[str] = []

    for source, endpoint in FUNDAMENTAL_ENDPOINTS.items():
        try:
            rows = _fetch_json(endpoint)
            rows_by_source[source] = _latest_by_code(rows, codes)
            source_dates = [_roc_date(row.get("出表日期")) for row in rows]
            as_of_dates.extend(date for date in source_dates if date)
            source_status[source] = {
                "status": "ok",
                "endpoint": f"{TWSE_OPENAPI_BASE}/{endpoint}",
                "row_count": len(rows),
            }
        except Exception as exc:
            rows_by_source[source] = {}
            source_status[source] = {
                "status": "unavailable",
                "endpoint": f"{TWSE_OPENAPI_BASE}/{endpoint}",
                "detail": f"{type(exc).__name__}: {exc}",
            }

    monthly = rows_by_source.get("monthly_revenue", {})
    operating = rows_by_source.get("operating_analysis", {})
    income = rows_by_source.get("income_statement", {})
    balance = rows_by_source.get("balance_sheet", {})
    official_links = _official_links()
    result: dict[str, dict[str, Any]] = {}

    for code, meta in stocks_meta.items():
        op = operating.get(code, {})
        inc = income.get(code, {})
        bs = balance.get(code, {})
        rev = monthly.get(code, {})
        period = _period(op) or _period(inc)
        as_of = max(
            filter(
                None,
                (
                    _roc_date(op.get("出表日期")),
                    _roc_date(inc.get("出表日期")),
                    _roc_date(rev.get("出表日期")),
                ),
            ),
            default=None,
        )

        gross_margin = _format_percent(op.get("毛利率(%)(營業毛利)/(營業收入)"))
        operating_margin = _format_percent(op.get("營業利益率(%)(營業利益)/(營業收入)"))
        net_margin = _format_percent(op.get("稅後純益率(%)(稅後純益)/(營業收入)"))
        eps = _number(inc.get("基本每股盈餘（元）"))
        revenue = _format_million_from_thousand(inc.get("營業收入"))
        net_income = _format_million_from_thousand(inc.get("淨利（淨損）歸屬於母公司業主"))

        parent_net_income = _number(inc.get("淨利（淨損）歸屬於母公司業主"))
        parent_equity = _number(bs.get("歸屬於母公司業主之權益合計"))
        annualized_roe = None
        if parent_net_income is not None and parent_equity:
            annualized_roe = parent_net_income / parent_equity * 4 * 100

        current_quarter = None
        if period and any(value is not None for value in (revenue, operating_margin, net_income, eps)):
            current_quarter = {
                "period": period,
                "revenue": revenue or "待更新",
                "operating_margin": operating_margin or "待更新",
                "net_income": net_income or "待更新",
                "eps": f"{eps:.2f} 元" if eps is not None else "待更新",
            }

        monthly_period = str(rev.get("資料年月", "")).strip()
        monthly_year = _number(monthly_period[:3]) if len(monthly_period) >= 5 else None
        monthly_month = monthly_period[3:5] if len(monthly_period) >= 5 else ""
        monthly_label = None
        if monthly_year is not None and monthly_month:
            monthly_growth = _format_signed_percent(rev.get("營業收入-去年同月增減(%)"))
            monthly_change = _format_signed_percent(rev.get("營業收入-上月比較增減(%)"))
            monthly_revenue = _format_million_from_thousand(rev.get("營業收入-當月營收"))
            monthly_label = (
                f"{int(monthly_year) + 1911}-{monthly_month} 營收 {monthly_revenue or '待更新'}"
                f"；月增 {monthly_change or '待更新'}；年增 {monthly_growth or '待更新'}"
            )

        event_label, event_status = _refresh_event_label(
            meta.get("earnings_date"), current.date()
        )
        values: dict[str, Any] = {
            "fundamental_as_of": as_of,
            "event_checked_at": current.isoformat(timespec="seconds"),
            "event_status": event_status,
            "earnings_date": event_label,
            "official_source_links": official_links,
        }
        if gross_margin:
            values["gross_margin"] = f"{gross_margin} ({period})" if period else gross_margin
        if net_margin:
            values["net_margin"] = f"{net_margin} ({period})" if period else net_margin
        if annualized_roe is not None:
            values["roe"] = f"{annualized_roe:.1f}% (單季年化, {period})"
        if eps is not None:
            values["eps_single"] = f"{eps:.2f} 元 ({period})" if period else f"{eps:.2f} 元"
        if monthly_label:
            values["latest_monthly_revenue"] = monthly_label
        if current_quarter:
            values["latest_quarter"] = current_quarter

        result[code] = values

    successful_sources = sum(status.get("status") == "ok" for status in source_status.values())
    status = "ok" if successful_sources == len(FUNDAMENTAL_ENDPOINTS) else "partial"
    return result, {
        "status": status,
        "updated_at": current.strftime("%Y-%m-%d %H:%M:%S"),
        "as_of": max(as_of_dates, default=None),
        "source": "TWSE OpenAPI fundamentals + MOPS event-calendar reference",
        "sources": source_status,
    }


if __name__ == "__main__":
    print("This module is imported by the quote and cloud update pipelines.")
