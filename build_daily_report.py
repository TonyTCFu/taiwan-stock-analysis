#!/usr/bin/env python3
"""Build a dated, source-attributed after-close report from published data."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "stock_data.json"
REPORT_DIR = ROOT / "REPORTS" / "daily"
TIMEZONE = ZoneInfo("Asia/Taipei")


def value(item: object) -> str:
    """Display missing fields explicitly without treating a check as new data."""
    return str(item) if item not in (None, "", "-") else "未取得"


def source_line(name: str, url: str, status: object, checked: object, published: object = None) -> str:
    return f"- {name}：{value(status)}；資料日期 {value(published)}；檢查時間 {value(checked)}；來源 {url}"


def render_report(payload: dict, now: dt.datetime) -> str:
    """Summarize observed fields and expose every missing or unverified layer."""
    checked = payload.get("content_checked_at")
    sources = payload.get("content_sources") or {}
    fundamental = payload.get("fundamental_status") or {}
    fundamental_sources = fundamental.get("sources") or {}
    quote_sync = payload.get("quote_sync_status") or payload.get("quote_status") or {}
    institutional = payload.get("institutional_status") or {}
    institutional_label = institutional.get("status")
    if institutional_label == "ok" and payload.get("institutional_as_of", "") < str(payload.get("market_as_of") or ""):
        institutional_label = "當日待發布／尚未取得，保留最近成功結算值"
    lines = [
        f"# 台股龍頭股收盤日報｜{now.date().isoformat()}",
        "",
        f"生成時間：{now.isoformat(timespec='minutes')}（台北）",
        f"涵蓋標的：{len(payload.get('stocks') or [])} 檔",
        f"資料版本：{value(payload.get('cache_version'))}",
        "",
        "## 更新狀態與來源",
        "",
        source_line("行情（Shioaji Snapshot／TWSE MIS 網關）", "https://futienchun-com-dashboard.onrender.com/api/live-quotes", quote_sync.get("status"), quote_sync.get("checked_at") or payload.get("quote_updated_at"), payload.get("market_as_of")),
        source_line("三大法人（TWSE T86）", "https://www.twse.com.tw/rwd/zh/fund/T86", institutional_label, institutional.get("retrieved_at"), payload.get("institutional_as_of")),
    ]
    for key, label in (("monthly_revenue", "月營收"), ("operating_analysis", "營益分析"), ("income_statement", "損益表"), ("balance_sheet", "資產負債表")):
        item = fundamental_sources.get(key) or {}
        lines.append(source_line(label, item.get("endpoint") or "來源網址未提供", item.get("status"), item.get("checked_at") or payload.get("fundamental_checked_at"), item.get("published_at") or "來源發布日未取得；資料期間見逐檔月份／季度"))
        if item.get("detail"):
            lines.append(f"  - 失敗原因：{item['detail']}")
    for key, label in (("announcements", "上市公司重大訊息"), ("market", "市場新聞"), ("industry", "產業新聞")):
        item = sources.get(key) or {}
        source_status = item.get("status")
        published = item.get("latest_published_at") or item.get("latest_matched_at")
        if key == "announcements" and source_status == "ok" and published and published < str(payload.get("market_as_of") or ""):
            source_status = "當日資料待發布／尚未取得，來源仍為上一發布日"
        lines.append(source_line(label, item.get("source") or "來源網址未提供", source_status, item.get("checked_at"), published))
        if item.get("detail"):
            lines.append(f"  - 失敗原因：{item['detail']}")
    company_status = sources.get("company_news") or {}
    lines.append(f"- 個股新聞：{value(company_status.get('status'))}；成功標的 {value(company_status.get('successful_stocks'))}/{len(payload.get('stocks') or [])}；檢查時間 {value(company_status.get('checked_at'))}；來源 Google 新聞 RSS／原始媒體（逐則附連結）")
    for key, label in (("market", "市場新聞"), ("industry", "產業新聞")):
        lines += ["", f"## {label}", ""]
        for item in (payload.get("news_feeds") or {}).get(key, [])[:5]:
            lines.append(f"- {value(item.get('published_at'))} {value(item.get('title'))}；來源 {value(item.get('source'))} {value(item.get('url'))}")
    lines += [
        "",
        "## 資料邊界",
        "",
        "- TWSE 財務出表日期是資料快照日期，不等於公司當天發布新財報；公司原始公告日未提供時不推定，實際資料期間見各股票月份／季度。",
        "- 產業新聞沿用中央社科技 RSS 原始分類，未做相關性排序；來源可能夾帶非產業新聞。",
        "- 法說行事曆與簡報全文：未接入可核驗的完整來源；僅收錄已擷取之重大訊息，不代表所有法說。核對入口 https://mops.twse.com.tw/mops/web/t100sb02_1",
        "- 研究評分／投資策略：本專案人工研究快照，不是每日自動核實的官方資料；請見各股票研究核對日與來源連結。",
        "",
        "## 逐檔資料",
        "",
    ]
    stocks = sorted(payload.get("stocks") or [], key=lambda stock: -(stock.get("score") or 0))
    for stock in stocks:
        flow = stock.get("institutional_flow") or {}
        quarter = stock.get("latest_quarter") or {}
        lines += [
            f"### {value(stock.get('code'))} {value(stock.get('name'))}",
            f"- 行情：NT$ {value(stock.get('last_price'))}；漲跌 {value(stock.get('change_pct'))}%；行情日期 {value(payload.get('market_as_of'))}；來源 {value(stock.get('quote_source') or payload.get('data_source'))}。",
            f"- 法人：合計 {value(flow.get('total_net'))}；結算日 {value(flow.get('date'))}；來源 TWSE T86。",
            f"- 月營收：{value(stock.get('latest_monthly_revenue'))}；來源 TWSE OpenAPI t187ap05_L。",
            f"- 季報：{value(quarter.get('period'))}；EPS {value(quarter.get('eps'))}（官方年初累計口徑；已核驗單季例外依原始資料）；營益率 {value(quarter.get('operating_margin'))}；來源 TWSE OpenAPI t187ap17_L／t187ap06_L_ci。",
        ]
        announcements = stock.get("official_announcements") or []
        if announcements:
            for item in announcements[:2]:
                lines.append(f"- 公告：{value(item.get('published_at'))} {value(item.get('title'))}；來源 {value(item.get('source'))} {value(item.get('url'))}")
        else:
            lines.append("- 公告：目前無已擷取的該股公告；不等於交易所或 MOPS 無公告。")
        news = stock.get("company_news") or []
        if news:
            for item in news[:2]:
                lines.append(f"- 新聞：{value(item.get('published_at'))} {value(item.get('title'))}；來源 {value(item.get('source'))} {value(item.get('url'))}")
        else:
            lines.append("- 新聞：未取得可核對的個股新聞。")
        links = [item for item in stock.get("source_links") or [] if item.get("url")]
        lines.append(f"- 研究核對日：{value(stock.get('research_checked_at'))}；研究資料來源：" + ("；".join(f"{value(item.get('label'))} {item['url']}" for item in links) if links else "未標註，需人工複核"))
        lines.append("")
    lines += ["## 使用限制", "", "檢查時間只表示已嘗試抓取，不代表該來源當天有發布新資料。新聞標題為來源原文，未經事實核查；不得當成投資建議。來源抓取失敗時看板可能保留最後成功值，請以上方資料日期判斷新鮮度。", ""]
    return "\n".join(lines)


def write_report(payload: dict, now: dt.datetime | None = None) -> tuple[Path, Path]:
    now = (now or dt.datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    report = render_report(payload, now)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    dated = REPORT_DIR / f"{now.date().isoformat()}.md"
    latest = REPORT_DIR / "index.html"
    dated.write_text(report, encoding="utf-8")
    escaped = html.escape(report)
    linked = re.sub(r"https://[^\s；]+", lambda match: f'<a href="{match.group(0)}" rel="noopener noreferrer">{match.group(0)}</a>', escaped)
    latest.write_text("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>台股龍頭股收盤日報</title><style>body{background:#101716;color:#e4efea;font:16px/1.7 system-ui;margin:0;padding:1rem}main{max-width:960px;margin:auto}a{color:#69d6bc}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}</style></head><body><main><p><a href=\"../../\">返回 Dashboard</a></p><pre>" + linked + "</pre></main></body></html>\n", encoding="utf-8")
    return dated, latest


if __name__ == "__main__":
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print(*(str(path) for path in write_report(data)), sep="\n")
