#!/usr/bin/env python3
"""Refresh public disclosures, fundamentals, and news independently of quotes."""

from __future__ import annotations

import datetime as dt
import email.utils
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fetch_shioaji_data import STOCKS_META
from fundamental_data import TWSE_OPENAPI_BASE, _fetch_json, _roc_date, fetch_fundamental_snapshot

OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "stock_data.json"
ANNOUNCEMENTS_URL = f"{TWSE_OPENAPI_BASE}/t187ap04_L"
NEWS_FEEDS = {
    "market": ("中央社財經", "https://feeds.feedburner.com/rsscna/finance"),
    "industry": ("中央社科技", "https://feeds.feedburner.com/rsscna/technology"),
}
CACHE_VERSION = "dashboard-r5"
COMPANY_ALIASES = {"2330": "台積電", "2383": "台光電", "2317": "鴻海"}


def taipei_now() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds")


def announcement_rows(rows: list[dict[str, Any]], codes: set[str]) -> dict[str, list[dict[str, str]]]:
    """Keep only exact company-code matches and source-provided filing dates."""
    result: dict[str, list[dict[str, str]]] = {code: [] for code in codes}
    for row in rows:
        code = str(row.get("公司代號", "")).strip()
        if code not in result:
            continue
        title = re.sub(r"\s+", " ", str(row.get("主旨 ") or row.get("主旨") or "")).strip()
        published = _roc_date(row.get("發言日期"))
        if not title or not published:
            continue
        result[code].append({
            "title": title[:220],
            "published_at": published,
            "source": "TWSE 上市公司每日重大訊息",
            "url": ANNOUNCEMENTS_URL,
            "category": "investor_conference" if "法說" in title or "法人說明會" in title else "company_disclosure",
        })
    for code in codes:
        result[code] = sorted(result[code], key=lambda item: item["published_at"], reverse=True)[:5]
    return result


def parse_rss(xml_data: bytes, source: str) -> list[dict[str, str]]:
    """Read publisher-provided headlines without inventing summaries or impact."""
    root = ET.fromstring(xml_data)
    items: list[dict[str, str]] = []
    for item in root.findall("./channel/item"):
        title = " ".join((item.findtext("title") or "").split())
        url = (item.findtext("link") or "").strip()
        raw_date = item.findtext("pubDate") or ""
        try:
            parsed = email.utils.parsedate_to_datetime(raw_date)
            published = parsed.astimezone(ZoneInfo("Asia/Taipei")).isoformat(timespec="minutes")
        except (TypeError, ValueError):
            continue
        if title and url.startswith("https://"):
            publisher = (item.findtext("source") or "").strip()
            items.append({"title": title[:220], "url": url, "published_at": published, "source": f"{source} / {publisher}" if publisher else source})
    return sorted(items, key=lambda item: item["published_at"], reverse=True)[:30]


def fetch_news(url: str, source: str) -> list[dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "TaiwanStockDashboard/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return parse_rss(response.read(), source)


def refresh_content(payload: dict[str, Any], checked_at: str | None = None) -> dict[str, Any]:
    """Update each source separately, preserving last good values on source failure."""
    now = checked_at or taipei_now()
    stocks = payload.get("stocks")
    if not isinstance(stocks, list) or not stocks:
        raise ValueError("Published stock data is missing")
    by_code = {str(stock.get("code")): stock for stock in stocks if isinstance(stock, dict)}
    status = payload.setdefault("content_sources", {})

    try:
        updates, source_status = fetch_fundamental_snapshot(STOCKS_META)
        for code, update in updates.items():
            stock = by_code.get(code)
            if stock is None:
                continue
            for field in ("gross_margin", "net_margin", "roe", "latest_monthly_revenue", "fundamental_as_of"):
                if update.get(field) is not None:
                    stock[field] = update[field]
            latest = update.get("latest_quarter")
            if latest:
                prior = [row for row in stock.get("quarterly_earnings", []) if row.get("period") != latest["period"]]
                stock["quarterly_earnings"] = (prior + [latest])[-4:]
                stock["latest_quarter"] = latest
        payload["fundamental_checked_at"] = now
        if source_status.get("status") == "ok":
            payload["fundamental_updated_at"] = now
            payload["fundamental_as_of"] = source_status.get("as_of")
        payload["fundamental_status"] = source_status
        status["fundamentals"] = {"status": source_status.get("status"), "checked_at": now}
    except Exception as exc:
        status["fundamentals"] = {"status": "unavailable", "checked_at": now, "detail": type(exc).__name__}

    try:
        filings = announcement_rows(_fetch_json("t187ap04_L"), set(by_code))
        for code, current in filings.items():
            if current:
                existing = by_code[code].get("official_announcements", [])
                merged = {(item["title"], item["published_at"]): item for item in existing if isinstance(item, dict) and item.get("title") and item.get("published_at")}
                merged.update({(item["title"], item["published_at"]): item for item in current})
                by_code[code]["official_announcements"] = sorted(merged.values(), key=lambda item: item["published_at"], reverse=True)[:5]
        latest = max((item["published_at"] for rows in filings.values() for item in rows), default=None)
        status["announcements"] = {"status": "ok", "checked_at": now, "latest_matched_at": latest, "source": ANNOUNCEMENTS_URL}
    except Exception as exc:
        status["announcements"] = {"status": "unavailable", "checked_at": now, "detail": type(exc).__name__}

    feeds = payload.setdefault("news_feeds", {})
    full_feeds: list[dict[str, str]] = []
    for category, (source, url) in NEWS_FEEDS.items():
        try:
            items = fetch_news(url, source)
            if not items:
                raise ValueError("Feed has no dated headlines")
            feeds[category] = items[:12]
            full_feeds.extend(items)
            status[category] = {"status": "ok", "checked_at": now, "latest_published_at": items[0]["published_at"], "source": url}
        except Exception as exc:
            status[category] = {"status": "unavailable", "checked_at": now, "detail": type(exc).__name__}

    all_news = full_feeds or [item for feed in feeds.values() if isinstance(feed, list) for item in feed]
    def fetch_company(code: str) -> tuple[str, list[dict[str, str]]]:
        name = COMPANY_ALIASES.get(code) or str(STOCKS_META[code]["name"])
        query = urllib.parse.urlencode({"q": f'"{name}" 股票', "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"})
        items = fetch_news(f"https://news.google.com/rss/search?{query}", "Google 新聞")
        return code, [item for item in items if name in item["title"]][:5]

    company_results: dict[str, list[dict[str, str]]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_company, code): code for code in by_code if code in STOCKS_META}
        for future in as_completed(futures):
            try:
                code, items = future.result()
                if items:
                    company_results[code] = items
            except Exception:
                pass
    for code, stock in by_code.items():
        name = str(STOCKS_META.get(code, {}).get("name", "")).strip()
        aliases = {name, COMPANY_ALIASES.get(code, "")}
        if name:
            fallback = sorted(
                (item for item in all_news if any(alias and alias in item.get("title", "") for alias in aliases)),
                key=lambda item: item["published_at"], reverse=True,
            )[:5]
            if company_results.get(code) or fallback:
                stock["company_news"] = company_results.get(code) or fallback
    status["company_news"] = {"status": "ok" if company_results else "partial", "checked_at": now, "successful_stocks": len(company_results), "expected_stocks": len(STOCKS_META)}
    payload["cache_version"] = f"{now[:16].replace('-', '').replace(':', '').replace('T', '-')}-{CACHE_VERSION}"
    payload["content_checked_at"] = now
    return payload


def main(quote_result: int | None = None) -> int:
    try:
        payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if quote_result is not None:
            payload["quote_sync_status"] = {
                "status": "ok" if quote_result == 0 else "unavailable",
                "checked_at": taipei_now(),
            }
        updated = refresh_content(payload)
        OUTPUT_PATH.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: content sync could not save valid stock data: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
