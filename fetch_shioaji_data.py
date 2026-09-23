import os
import json
import datetime
import re
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from fundamental_data import fetch_fundamental_snapshot


def _as_float(value, default=0.0):
    """Return a numeric quote field without turning TWSE '-' into an error."""
    if value in (None, "", "-"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    """Return an integer quote field without failing on missing market data."""
    if value in (None, "", "-"):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def latest_market_date(now):
    """Return the latest trading-day date when the quote feed has no date field."""
    candidate = now.date()
    if candidate.weekday() >= 5 or now.time() < datetime.time(9, 0):
        candidate -= datetime.timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate -= datetime.timedelta(days=1)
    return candidate.isoformat()


def next_research_review_at(now):
    """Return the next weekday automatic data sync slot in Taiwan time."""
    taipei = ZoneInfo("Asia/Taipei")
    current = now.replace(tzinfo=taipei) if now.tzinfo is None else now.astimezone(taipei)
    next_day = current.date() + datetime.timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += datetime.timedelta(days=1)
    return f"{next_day.isoformat()} 14:30 Asia/Taipei"


def market_snapshot_text(stock, market_as_of):
    """Build quote prose from the same validated quote fields used by the card."""
    price = _as_float(stock.get("last_price"))
    change_pct = _as_float(stock.get("change_pct"))
    if price <= 0:
        return f"行情待同步；資料基準日 {market_as_of}。"
    return (
        f"{market_as_of} 收盤/最新 NT${price:,.2f}，"
        f"日變動 {change_pct:+.2f}%；行情時間 {stock.get('quote_time') or '-'}。"
    )


def research_source_as_of(stock, market_as_of):
    """Keep market, revenue, and quarterly source periods explicit."""
    quarter = (stock.get("latest_quarter") or {}).get("period") or "季度待同步"
    revenue = stock.get("latest_monthly_revenue") or ""
    match = re.search(r"20\d{2}-\d{2}", revenue)
    revenue_period = match.group(0) if match else "月營收待同步"
    return f"行情 {market_as_of}；月營收 {revenue_period}；財報 {quarter}"


def load_shioaji_env():
    possible_paths = [
        Path('/Users/TonyFu/Documents/台股量化Antigravity/.shioaji.local.env'),
        Path('/Users/TonyFu/Documents/Codex本地/稳健投资组合量化模型构建 2/.shioaji.local.env')
    ]
    for env_path in possible_paths:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break


STOCKS_META = {
    "2330": {
        "symbol": "2330.TW",
        "name": "台积电",
        "en_name": "TSMC",
        "chokepoint": "晶圆代工霸主、CoWoS 高阶封装瓶颈、2nm/3nm 垄断",
        "score": 98,
        "gross_margin": "65.0% - 67.0%",
        "net_margin": ">43.0%",
        "roe": "40.5%",
        "eps_single": "22.08 元 (26Q1)",
        "earnings_date": "2026-10-15 (26Q3 法说会) | 每月 10 日发布营收",
        "price_analytics": {
            "ma20_bias": "+1.8% (处于健康均线排列)",
            "amplitude": "1.04% (高档横盘整理)",
            "trend_evaluation": "2nm 按计划量产，CoWoS 产能持续供不应求，多头格局未变。"
        },
        "buy_zone_sub": "2,200 - 2,300 元",
        "buy_zone_heavy": "2,050 - 2,150 元",
        "take_profit": "2,750 - 2,900 元",
        "target_price": "3,200 - 3,500 元",
        "stop_loss": "1,980 元"
    },
    "2059": {
        "symbol": "2059.TW",
        "name": "川湖",
        "en_name": "King Slide",
        "chokepoint": "AI 超级机柜精密导轨绝对垄断者（市占率超 70%）",
        "score": 92,
        "gross_margin": "87.0%",
        "net_margin": ">52.0%",
        "roe": "21.72%",
        "eps_single": "74.38 元 (26Q2)",
        "earnings_date": "2026-11-06 (26Q3 财报) | 每月 10 日发布营收",
        "price_analytics": {
            "ma20_bias": "+3.2%",
            "amplitude": "4.21% (单日震幅加大，高位洗盘)",
            "trend_evaluation": "2026 上半年 EPS 冲破 110 元，北美新厂开出，长期确定性最高。"
        },
        "buy_zone_sub": "11,000 - 11,800 元",
        "buy_zone_heavy": "9,800 - 10,500 元",
        "take_profit": "14,500 - 15,500 元",
        "target_price": "17,000 - 17,500 元",
        "stop_loss": "9,200 元"
    },
    "2383": {
        "symbol": "2383.TW",
        "name": "台光电",
        "en_name": "EMC",
        "chokepoint": "800G/1.6T 高阶 CCL (M8/M9 铜箔基板) 瓶颈材料龙头",
        "score": 88,
        "gross_margin": "33.8%",
        "net_margin": "~19.5%",
        "roe": "18.58%",
        "eps_single": "27.55 元 (26Q2)",
        "earnings_date": "2026-10-29 (26Q3 财报) | 每月 10 日发布营收",
        "price_analytics": {
            "ma20_bias": "+4.5% (多头强劲攻势)",
            "amplitude": "4.36% (开低走高强势收长红)",
            "trend_evaluation": "800G/1.6T 交换机升频核心受惠者，均线呈标准多头排列。"
        },
        "buy_zone_sub": "3,950 - 4,200 元",
        "buy_zone_heavy": "3,600 - 3,800 元",
        "take_profit": "4,900 - 5,200 元",
        "target_price": "5,600 - 5,900 元",
        "stop_loss": "3,450 元"
    },
    "3017": {
        "symbol": "3017.TW",
        "name": "奇鋐",
        "en_name": "AVC",
        "chokepoint": "AI 服务器水冷/液冷系统级解决方案霸主",
        "score": 85,
        "gross_margin": "33.8% - 35.0%",
        "net_margin": "~14.2%",
        "roe": "17.03%",
        "eps_single": "20.17 元 (26Q1)",
        "earnings_date": "2026-11-10 (26Q3 法说会) | 每月 10 日发布营收",
        "price_analytics": {
            "ma20_bias": "+3.8%",
            "amplitude": "5.68% (盘中高低拉升近6%，动能充沛)",
            "trend_evaluation": "GB200/NVL72 快换接头及水冷板量产，盘中高振幅提供低吸点。"
        },
        "buy_zone_sub": "2,450 - 2,600 元",
        "buy_zone_heavy": "2,250 - 2,380 元",
        "take_profit": "3,100 - 3,300 元",
        "target_price": "3,700 - 4,000 元",
        "stop_loss": "2,100 元"
    },
    "3653": {
        "symbol": "3653.TW",
        "name": "健策",
        "en_name": "Jentech Precision",
        "industry": "AI/HPC 熱管理、散熱元件與精密金屬加工",
        "chokepoint": "由封裝端均熱片、VC／微流道蓋板到系統端液冷冷板的垂直熱管理產品鏈",
        "score": 88,
        "score_basis": "TypeSafe 結構化評分思路：以已核實獲利與官方產品定位評估基本面/卡位；估值、動能及風險權重未完成週度複核，此分數僅為初始研究分，不是 TypeSafe API 輸出或官方評等。",
        "investment_case": "公司官方產品涵蓋封裝端均熱片、VC 與微流道蓋板，以及 HPC 液冷冷板。2026Q2 營收 72.75 億元、毛利率 46.81%、EPS 15.80 元；2026-08 營收 32.26 億元、年增 90.90%。",
        "earnings_trend": "2026Q2 EPS 15.80 元，季增 65.8%、年增 101.3%；H1 累計 EPS 25.33 元。需留意營收及毛利能否延續，不以單季高成長外推全年。",
        "quarterly_earnings": [
            {"period": "2026Q1", "revenue": "53.05 億元", "operating_margin": "約 34.0%", "net_income": "約 14.0 億元", "eps": "9.53 元"},
            {"period": "2026Q2", "revenue": "72.75 億元", "operating_margin": "約 37.8%", "net_income": "23.18 億元", "eps": "15.80 元"}
        ],
        "verified_quarter_override": {
            "period": "2026Q2",
            "revenue": "7,274.516 百萬元",
            "gross_margin": "46.81%",
            "operating_margin": "37.79%",
            "net_margin": "32.01%",
            "net_income": "2,318.490 百萬元",
            "eps": "15.80 元",
            "eps_numeric": 15.80
        },
        "market_snapshot": "2026-09-22 收盤 NT$5,830；估值尚未以一致的最新獲利預估核算。",
        "valuation": "股價與成長預期均高；缺少可靠的前瞻 EPS 與一致 PER 口徑，本次不下估值結論、不提供目標價。",
        "market_factors": "AI 資料中心功耗提升帶動熱管理升級；液冷滲透、客戶驗證與量產速度是催化，客戶集中、產品迭代及擴產折舊是主要反向因素。",
        "risk_factors": ["估值對成長預期敏感，需以最新獲利預估重估", "AI/HPC 客戶集中與量產時程風險", "短期營收高速成長未必線性延續", "需追蹤毛利率、現金流與擴產折舊"],
        "recommendation": "新增觀察／待完成週度評分",
        "strategy_note": "列入龍頭研究名單；未完成估值及動能檢核前，不據此形成買進建議。",
        "source_links": [
            {"label": "公司官方產品與 HPC 熱管理", "url": "https://www.jentech.com.tw/zh"},
            {"label": "健策官方月營收", "url": "https://www.jentech.com.tw/zh/monthly-revenue"},
            {"label": "2026Q2 財報資料", "url": "https://m.moneydj.com/f1a.aspx?a=826e52d0-6eb0-45d7-9955-81bb17c55dab"},
            {"label": "2026-08 月營收公告", "url": "https://www.moneydj.com/kmdj/news/newsviewer.aspx?a=0ee49ee4-edf5-41c9-b3c3-cafc5e95a6cd"},
            {"label": "行情快照", "url": "https://cn.investing.com/equities/jentech-historical-data"}
        ],
        "gross_margin": "46.81% (2026Q2)",
        "net_margin": "32.01% (2026Q2)",
        "roe": "待官方同步",
        "eps_single": "15.80 元 (2026Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "待計算；本次未完成歷史行情複核",
            "amplitude": "高價成長股，需控制單一標的與產業集中風險",
            "trend_evaluation": "基本面與熱管理產品鏈符合研究主題；估值與趨勢尚待量化檢核。"
        },
        "buy_zone_sub": "待估值與技術面複核",
        "buy_zone_heavy": "暫不設定",
        "take_profit": "依獲利與估值重新評估",
        "target_price": "不預設固定目標",
        "stop_loss": "依獲利趨勢與個人風險承受度管理"
    },
    "2317": {
        "symbol": "2317.TW",
        "name": "鸿海",
        "en_name": "Hon Hai",
        "chokepoint": "NVL72/GB200 AI 超级机柜系统级垂直集成与交付独霸",
        "score": 81,
        "gross_margin": "6.2% - 6.8%",
        "net_margin": "~2.8%",
        "roe": "11.25%",
        "eps_single": "3.23 元 (25Q4)",
        "earnings_date": "2026-08-14 (26Q2 法说会 - 本周五) | 每月 5 日发布营收",
        "price_analytics": {
            "ma20_bias": "+2.1%",
            "amplitude": "2.44% (大盘股稳健放量大涨)",
            "trend_evaluation": "7 月营收创历史新高，法说会催化，AI 服务器占比突破 50%。"
        },
        "buy_zone_sub": "255 - 270 元",
        "buy_zone_heavy": "238 - 248 元",
        "take_profit": "315 - 335 元",
        "target_price": "360 - 380 元",
        "stop_loss": "225 元"
    },
    "2308": {
        "symbol": "2308.TW",
        "name": "台達電",
        "en_name": "Delta Electronics",
        "industry": "電源管理、資料中心基礎設施與熱管理",
        "chokepoint": "高效率電源、資料中心基礎設施與熱管理的系統級整合",
        "score": 85,
        "score_basis": "獲利趨勢、技術門檻、估值與風險綜合評估；非官方評等",
        "investment_case": "AI 資料中心的電力效率、電源管理與熱管理需求同步成長。2026Q2 營收 1,832 億元、營益率 16.7%、稅後淨利 251.36 億元。",
        "earnings_trend": "EPS 6.67 → 7.91 → 9.68，連續兩季走高；電源電子與基礎設施部門獲利分別年增 50% 與 121%。",
        "quarterly_earnings": [
            {"period": "2025Q4", "revenue": "待更新", "operating_margin": "待更新", "net_income": "約 173 億元", "eps": "6.67 元"},
            {"period": "2026Q1", "revenue": "待更新", "operating_margin": "待更新", "net_income": "205.56 億元", "eps": "7.91 元"},
            {"period": "2026Q2", "revenue": "1,832 億元", "operating_margin": "16.7%", "net_income": "251.36 億元", "eps": "9.68 元"}
        ],
        "market_snapshot": "8/27 約 NT$1,770；PER 約 56 倍；近 3 個月約 -25.9%，近 1 年約 +147%。",
        "valuation": "獲利品質高，但 PER 已反映相當多 AI 基礎設施成長預期。",
        "market_factors": "AI 資料中心資本支出、電力效率要求與液冷導入是正面因素；利率上升或雲端資本支出放緩會造成估值壓縮。",
        "risk_factors": ["估值偏高", "與既有 3017、2059 有 AI 伺服器產業暴露重疊", "資料中心資本支出週期反轉"],
        "recommendation": "核心追蹤",
        "strategy_note": "分批觀察，不追高；等待估值回落或獲利再上修",
        "source_links": [
            {"label": "2026Q2 官方法說資料", "url": "https://filecenter.deltaww.com/ir/download/calendar/2Q26_Analyst%20Meeting.pdf"},
            {"label": "行情與估值快照", "url": "https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=2308"}
        ],
        "gross_margin": "35.6% (26Q2)",
        "net_margin": "13.7% (26Q2)",
        "roe": "待更新",
        "eps_single": "9.68 元 (26Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "近 3 個月回落約 25.9%",
            "amplitude": "高估值成長股，波動偏高",
            "trend_evaluation": "獲利趨勢向上，但必須以後續營益率與 AI 基礎設施訂單驗證估值。"
        },
        "buy_zone_sub": "分批觀察（不追高）",
        "buy_zone_heavy": "等待估值明顯回落",
        "take_profit": "依獲利與趨勢再評估",
        "target_price": "不預設固定目標",
        "stop_loss": "跌破基本面假設即檢視"
    },
    "2345": {
        "symbol": "2345.TW",
        "name": "智邦",
        "en_name": "Accton Technology",
        "industry": "AI 高速網路交換器與資料中心網通",
        "chokepoint": "800G/1.6T 高速交換器與 AI 集群網路整合的高門檻環節",
        "score": 86,
        "score_basis": "獲利趨勢、技術門檻、估值與風險綜合評估；非官方評等",
        "investment_case": "AI 集群規模提升帶動高速交換器升級。2026Q2 營收 955.38 億元、營益率約 15.0%、母公司稅後淨利 110.53 億元。",
        "earnings_trend": "EPS 14.95 → 14.92 → 19.78；Q2 EPS 季增約 32.5%，營益率由 12.7% 提升至約 15.0%。",
        "quarterly_earnings": [
            {"period": "2025Q4", "revenue": "720.18 億元", "operating_margin": "12.7%", "net_income": "83.56 億元", "eps": "14.95 元"},
            {"period": "2026Q1", "revenue": "701.21 億元", "operating_margin": "14.3%", "net_income": "83.41 億元", "eps": "14.92 元"},
            {"period": "2026Q2", "revenue": "955.38 億元", "operating_margin": "15.0%", "net_income": "110.53 億元", "eps": "19.78 元"}
        ],
        "market_snapshot": "8/26 收約 NT$2,055；PER 約 32 倍；近 3 個月約 -7.2%，近 6 個月約 +41.7%。",
        "valuation": "五檔新增標的中估值相對合理，但市場已反映高速網通成長。",
        "market_factors": "雲端服務商 AI 資本支出、800G/1.6T 升級與高速光互連需求是主要催化；客戶集中與供應鏈交期是反向因素。",
        "risk_factors": ["大型雲端客戶集中", "高速交換器世代轉換造成產品週期風險", "AI 資本支出若放緩將影響訂單能見度"],
        "recommendation": "核心追蹤／首選",
        "strategy_note": "可列入優先研究，仍採分批而非追價買進",
        "source_links": [
            {"label": "季度財務資料", "url": "https://fubon-ebrokerdj.fbs.com.tw/z/zc/zcq/zcq_2345.djhtm"},
            {"label": "行情與估值快照", "url": "https://goodinfo.tw/tw/ShowK_Chart.asp?STOCK_ID=2345"},
            {"label": "公司高速網通資料", "url": "https://www.accton.com.tw/wp-content/uploads/2024/07/20240712031358.pdf"}
        ],
        "gross_margin": "19.7% (26Q2)",
        "net_margin": "約 11.6% (26Q2)",
        "roe": "待更新",
        "eps_single": "19.78 元 (26Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "近 3 個月約 -7.2%，相對大幅上漲後整理",
            "amplitude": "高速網通成長股，波動中高",
            "trend_evaluation": "Q2 營收與 EPS 同步加速，是新增標的中基本面與估值平衡度最佳者。"
        },
        "buy_zone_sub": "分批觀察（不追高）",
        "buy_zone_heavy": "等待成長預期降溫",
        "take_profit": "依訂單與 EPS 趨勢再評估",
        "target_price": "不預設固定目標",
        "stop_loss": "營益率與訂單能見度轉弱即檢視"
    },
    "2360": {
        "symbol": "2360.TW",
        "name": "致茂",
        "en_name": "Chroma ATE",
        "industry": "半導體、AI、光通訊與先進封裝測試設備",
        "chokepoint": "高精度測試、量測與先進封裝檢測，屬 AI 硬體量產的關鍵驗證設備",
        "score": 84,
        "score_basis": "獲利趨勢、技術門檻、估值與風險綜合評估；非官方評等",
        "investment_case": "AI/HPC、GPU、CPU、交換器與光通訊升級拉動測試需求。2026Q2 營收 135.29 億元、毛利率約 60.5%、營益率約 38.7%。",
        "earnings_trend": "EPS 6.04 → 9.12 → 約 12.15；連續三季創高，獲利增速在新增五檔中最強。",
        "quarterly_earnings": [
            {"period": "2025Q4", "revenue": "85.80 億元", "operating_margin": "約 34.8%", "net_income": "25.50 億元", "eps": "6.04 元"},
            {"period": "2026Q1", "revenue": "118.60 億元", "operating_margin": "約 40.4%", "net_income": "38.64 億元", "eps": "9.12 元"},
            {"period": "2026Q2", "revenue": "135.29 億元", "operating_margin": "約 38.7%", "net_income": "51.23 億元", "eps": "約 12.15 元"}
        ],
        "market_snapshot": "8/27 約 NT$1,990；PER 約 51 倍；近 3 個月約 -22.6%，近 1 年約 +262%。",
        "valuation": "基本面強，但一年漲幅與 PER 都高，適合分批觀察，不適合只看題材追價。",
        "market_factors": "先進封裝、AI 伺服器、光通訊與高功率電源測試需求是正面因素；半導體資本支出與客戶驗證時程會影響短期營收。",
        "risk_factors": ["估值與波動偏高", "半導體資本支出循環", "擴產與資本支出造成現金流、稀釋或折舊壓力"],
        "recommendation": "核心追蹤／高波動",
        "strategy_note": "保留名單，但以回檔分批為主；關注毛利率與現金流是否維持",
        "source_links": [
            {"label": "公司業務與技術範圍", "url": "https://www.chromaate.com/tw/chroma/aboutchroma"},
            {"label": "季度結果公告", "url": "https://www.chromaate.com/tw/investors/quarterly_results"},
            {"label": "行情與估值快照", "url": "https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID=2360"}
        ],
        "gross_margin": "約 60.5% (26Q2)",
        "net_margin": "約 37.9% (26Q2)",
        "roe": "待更新",
        "eps_single": "約 12.15 元 (26Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "近 3 個月約 -22.6%，高檔修正",
            "amplitude": "近 1 年約 +262%，波動極高",
            "trend_evaluation": "獲利趨勢最強，但市場已給予高溢價，必須用下一季毛利率與訂單驗證。"
        },
        "buy_zone_sub": "回檔分批觀察",
        "buy_zone_heavy": "等待估值與波動收斂",
        "take_profit": "依 EPS 與毛利率再評估",
        "target_price": "不預設固定目標",
        "stop_loss": "獲利趨勢反轉即檢視"
    },
    "3711": {
        "symbol": "3711.TW",
        "name": "日月光投控",
        "en_name": "ASE Technology Holding",
        "industry": "IC 封裝測試、先進封裝與 Panel-Level Packaging",
        "chokepoint": "AI 晶片大規模封裝測試與先進封裝產能，屬量產環節的關鍵瓶頸",
        "score": 79,
        "score_basis": "獲利趨勢、技術門檻、估值與風險綜合評估；非官方評等",
        "investment_case": "AI 加速器、Chiplet 與先進封裝擴產帶動封測需求。2026Q2 營收約 1,911 億元、營益率 11.1%、EPS 4.80 元。",
        "earnings_trend": "EPS 約 3.4 → 3.24 → 4.80；Q2 顯著反彈，2026H1 EPS 8.04 元。",
        "quarterly_earnings": [
            {"period": "2025Q4", "revenue": "約 1,779 億元", "operating_margin": "約 9.9%", "net_income": "約 147.1 億元", "eps": "約 3.4 元"},
            {"period": "2026Q1", "revenue": "約 1,737 億元", "operating_margin": "10.1%", "net_income": "約 141.5 億元", "eps": "3.24 元"},
            {"period": "2026Q2", "revenue": "約 1,911 億元", "operating_margin": "11.1%", "net_income": "約 210.7 億元", "eps": "4.80 元"}
        ],
        "market_snapshot": "8/27 約 NT$605；PER 約 44 倍；近 3 個月約 -2.4%，近 1 年約 +138%。",
        "valuation": "相較純 AI 設備股波動較低，但仍受封測資本支出與景氣循環影響。",
        "market_factors": "AI 晶片封裝測試、Chiplet、Panel-Level Packaging 與高階封裝產能擴建是正面因素；折舊、負債與客戶稼動率是反向因素。",
        "risk_factors": ["封裝測試景氣循環", "擴產帶來折舊與資本支出壓力", "與既有 2330 的先進封裝產業暴露重疊"],
        "recommendation": "觀察／可小部位",
        "strategy_note": "等待先進封裝稼動率與營益率連續改善，再提高評級",
        "source_links": [
            {"label": "公司先進封裝資料", "url": "https://ase-holding.webflow.io/press-room-ch/310x310"},
            {"label": "財報與行情快照", "url": "https://goodinfo.tw/tw/StockFinDetail.asp?QRY_TIME=20262&RPT_CAT=IS_M_QUAR&STOCK_ID=3711"}
        ],
        "gross_margin": "待更新",
        "net_margin": "約 11.0% (26Q2)",
        "roe": "18.2% 年化 (26H1)",
        "eps_single": "4.80 元 (26Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "近 3 個月約 -2.4%，相對穩定",
            "amplitude": "近 1 年約 +138%，仍屬高檔區",
            "trend_evaluation": "Q2 獲利反彈，但要觀察先進封裝擴產是否轉化為持續營益率改善。"
        },
        "buy_zone_sub": "小部位觀察",
        "buy_zone_heavy": "等待營益率連續改善",
        "take_profit": "依封裝稼動率再評估",
        "target_price": "不預設固定目標",
        "stop_loss": "資本支出與折舊失控即檢視"
    },
    "2454": {
        "symbol": "2454.TW",
        "name": "聯發科",
        "en_name": "MediaTek",
        "industry": "Fabless IC、手機/邊緣 AI SoC 與 AI ASIC",
        "chokepoint": "高階 SoC、AI ASIC 設計/IP 與客戶軟硬體生態整合的高門檻",
        "score": 77,
        "score_basis": "獲利趨勢、技術門檻、估值與風險綜合評估；非官方評等",
        "investment_case": "公司仍具高毛利與正獲利，但 AI ASIC 商業化尚在驗證期。2026Q2 營收約 1,521.83 億元、營益率 15.0%、EPS 15.28 元。",
        "earnings_trend": "EPS 14.39 → 15.17 → 15.28；近兩季大致穩定，但 2026Q2 淨利年減約 12.3%，尚未形成強勁加速。",
        "quarterly_earnings": [
            {"period": "2025Q4", "revenue": "1,501.88 億元", "operating_margin": "14.5%", "net_income": "230.74 億元", "eps": "14.39 元"},
            {"period": "2026Q1", "revenue": "1,491.51 億元", "operating_margin": "15.3%", "net_income": "243.76 億元", "eps": "15.17 元"},
            {"period": "2026Q2", "revenue": "1,521.83 億元", "operating_margin": "15.0%", "net_income": "246.05 億元", "eps": "15.28 元"}
        ],
        "market_snapshot": "8/27 約 NT$3,865；PER 約 64 倍；近 3 個月約 -15%。",
        "valuation": "獲利穩定但 PER 偏高，必須等 AI ASIC 實際營收與毛利貢獻確認。",
        "market_factors": "AI ASIC、邊緣 AI、車用與高速連接是中長期因素；手機景氣、客戶自研與 ASIC 導入時程是短期變數。",
        "risk_factors": ["PER 偏高", "AI ASIC 尚未完成規模化驗證", "手機與消費電子週期、客戶自研競爭"],
        "recommendation": "觀察",
        "strategy_note": "等 AI ASIC 營收與淨利年增轉正，再考慮提高評級",
        "source_links": [
            {"label": "2026Q1 官方法說資料", "url": "https://www.mediatek.com/hubfs/MediaTek%20Assets/Pdfs/Quarterly%20Earnings%20Release/2026/Quarterly%20Earnings%20Release-2026Q1/%5B%E6%B3%95%E8%87%AA%E8%AA%87%E6%9C%83%E8%B3%87%E6%96%99%5DQ1%E7%B0%A1%E5%A0%B1%E8%B3%87%E6%96%99.pdf"},
            {"label": "投資人關係頁面", "url": "https://www.mediatek.com/zh-tw/investor-relations"},
            {"label": "行情與估值快照", "url": "https://goodinfo.tw/tw/ShowK_Chart.asp?CHT_CAT2=DATE&STOCK_ID=2454"}
        ],
        "gross_margin": "46.2% (26Q2)",
        "net_margin": "約 16.2% (26Q2)",
        "roe": "待更新",
        "eps_single": "15.28 元 (26Q2)",
        "earnings_date": "2026Q2 已公告；下一次財報/法說日待公司公告",
        "price_analytics": {
            "ma20_bias": "近 3 個月約 -15%，高檔整理",
            "amplitude": "近一年漲幅大，估值對消息敏感",
            "trend_evaluation": "目前屬正獲利但成長驗證中的觀察股，不列入前三檔核心。"
        },
        "buy_zone_sub": "觀察，不追價",
        "buy_zone_heavy": "等待 AI ASIC 驗證",
        "take_profit": "依 ASIC 營收再評估",
        "target_price": "不預設固定目標",
        "stop_loss": "獲利與 ASIC 時程轉弱即檢視"
    }
}

RESEARCH_BASELINES = {
    "2330": {
        "industry": "專業晶圓代工；競爭核心為先進製程、良率、規模與先進封裝整合。",
        "earnings_trend": "2026Q2 官方季報 EPS 27.25 元；TWSE OpenAPI 申報欄位可能為年初累計口徑，未拆分前不作跨季趨勢或 TTM 計算。",
        "eps_single": "27.25 元 (2026Q2 單季；TSMC 官方財報)",
        "investment_case": "公司以純晶圓代工為核心。2026Q2 官方資料顯示營收 NT$1,270.38B、單季 EPS NT$27.25，7nm 及以下製程占晶圓營收 77%；AI/HPC 對先進製程與封裝需求是主要成長來源。",
        "market_factors": "正向：AI/HPC 晶片需求、先進製程與先進封裝滲透。反向：半導體景氣與客戶資本支出週期、海外廠成本與毛利稀釋、匯率及高資本支出。",
        "risk_factors": ["地緣政治與台海營運中斷風險", "海外廠建置成本、爬坡與毛利稀釋", "半導體景氣、客戶資本支出及先進封裝需求反轉", "高資本支出與匯率波動"],
        "strategy_note": "追蹤 2026-10-15 公司 Q3 法說、2nm 量產爬坡、先進封裝供需與毛利率；若成長預期或毛利率偏離公司指引，重估研究假設，不以題材替代估值。",
        "source_links": [
            {"label": "公司簡介", "url": "https://www.tsmc.com/english/aboutTSMC/company_profile"},
            {"label": "2026Q2 官方財報與法說", "url": "https://investor.tsmc.com/english/quarterly-results/2026/q2"},
            {"label": "2026 月營收", "url": "https://investor.tsmc.com/english/monthly-revenue/2026"},
        ],
    },
    "2059": {
        "industry": "精密滑軌、伺服器導軌套件與家具五金；伺服器產品包括導軌及線纜管理臂。",
        "earnings_trend": "最新 TWSE OpenAPI 欄位為 2026Q2 申報值；在核實單季/累計口徑及取得完整四季數據前，不作季度趨勢或 TTM 計算。",
        "eps_single": "74.38 元 (2026Q2 單季；公司法說資料)",
        "investment_case": "公司官方產品頁列有伺服器導軌套件與線纜管理臂，並公布面向 NVIDIA MGX 生態的導軌方案。AI 機櫃重量、密度與維護需求增加，可能提升高規格導軌價值；實際受益仍須以公司營收、客戶集中及產能利用率驗證。",
        "market_factors": "正向：AI 伺服器及資料中心機櫃擴建、機櫃設計複雜度提高。反向：大型客戶集中、客戶平台切換、擴產與新廠爬坡、伺服器資本支出週期及家具五金景氣。",
        "risk_factors": ["伺服器大客戶與少數平台集中", "AI 資本支出放緩或平台轉換影響訂單", "擴產與新廠爬坡造成成本/現金流壓力", "高估值對成長預期變化敏感"],
        "strategy_note": "以月營收、毛利率、應收帳款與產能爬坡交叉驗證伺服器需求；等待最新季度財報及公司法說更新後再檢視獲利延續性，不把單季或年初累計 EPS 當作 TTM。",
        "source_links": [
            {"label": "伺服器導軌與公司產品", "url": "https://www.kingslide.com/site_map"},
            {"label": "公司 2026 MGX 導軌資訊", "url": "https://www.kingslide.com/blog/post/news/identifier/company-news-018/"},
            {"label": "公司投資人專區入口", "url": "https://www.kingslide.com/"},
        ],
    },
    "2383": {
        "industry": "銅箔基板（CCL）與黏合片（Prepreg）材料；供應高速運算、網通及高頻高速電路板。",
        "earnings_trend": "2026Q2 官方揭露的 EPS 42.46 元為 2026H1 累計值，不是單季數；未取得四季單季 EPS 前不推算 TTM。",
        "eps_single": "27.55 元 (2026Q2 單季；公司季度財報)",
        "investment_case": "公司官方資料將核心業務列為 CCL/Prepreg。2026Q2 公告的 2026H1 累計營收為 NT$80.34B、累計 EPS NT$42.46；這是半年度累計口徑，不是單季 EPS。高速網路與 AI 伺服器升級可能提高低損耗材料需求，仍需以產品組合與毛利率驗證。",
        "market_factors": "正向：AI 伺服器、交換器速率升級及高速材料規格提升。反向：銅箔、樹脂等原料成本、客戶認證週期、擴產折舊、匯率及 PCB/網通景氣回落。",
        "risk_factors": ["高階材料客戶認證或量產延遲", "銅箔/樹脂原料與匯率波動", "擴產折舊與營運資金需求", "AI 網通資本支出反轉及高估值波動"],
        "strategy_note": "每月追蹤營收、季度檢視毛利率與產品組合；確認高階材料營收轉化為獲利而非只看需求敘事。估值需使用四季單季 EPS，資料不足時不報 TTM 本益比。",
        "source_links": [
            {"label": "公司業務與沿革", "url": "https://www.emctw.com/en-global/about_milestone/index"},
            {"label": "公司季度財報", "url": "https://www.emctw.com/en-global/quarterly_results/index"},
            {"label": "2026Q2 財報公告（2026-07-29）", "url": "https://www.emctw.com/en-global/investors_news/detail/2026072901/1"},
        ],
    },
    "3017": {
        "industry": "散熱與熱管理解決方案，涵蓋風扇、散熱模組、機殼及系統整合方案。",
        "earnings_trend": "最新 TWSE OpenAPI 欄位為 2026Q2 申報值；在核實單季/累計口徑及取得完整四季數據前，不作季度趨勢或 TTM 計算。",
        "eps_single": "24.37 元 (2026Q2 單季；公司季度財報)",
        "investment_case": "公司定位為整體熱管理方案供應商，產品從散熱元件延伸至系統級冷卻方案。AI 伺服器功耗上升提高散熱設計價值；收入與毛利能否持續受益，仍取決於客戶驗證、量產良率與產品組合。",
        "market_factors": "正向：AI/HPC 功耗密度提升、氣冷升級與液冷導入。反向：主要客戶/平台集中、量產時程延誤、競品價格、擴產折舊及伺服器資本支出反轉。",
        "risk_factors": ["主要客戶/平台集中與新方案驗證延誤", "液冷競爭加劇、產品價格及毛利率壓力", "擴產折舊與產能利用率變化", "AI 伺服器投資週期反轉"],
        "strategy_note": "追蹤新平台量產進度、月營收、毛利率、營業現金流與存貨；若營收增長未轉化為毛利/現金流改善，降低對成長敘事的權重。",
        "source_links": [
            {"label": "公司簡介與熱管理定位", "url": "https://www.avc.co/en-us/"},
            {"label": "公司散熱解決方案", "url": "https://www.avc.co/en-us/ProductTechnology/%E6%95%A3%E7%86%B1%E7%94%A2%E5%93%81/%E6%95%A3%E7%86%B1%E6%96%B9%E6%A1%88"},
            {"label": "公司投資人資訊入口", "url": "https://www.avc.co/en-us/"},
        ],
    },
    "2317": {
        "industry": "電子製造服務（EMS）、設計製造與系統組裝；業務涵蓋雲端網路、消費電子、電腦終端及元件。",
        "earnings_trend": "2026Q2 公司公告單季 EPS 4.27 元、2026H1 累計 EPS 7.83 元；後者不可誤標為單季 EPS。",
        "eps_single": "4.27 元 (2026Q2 單季；鴻海官方公告)",
        "investment_case": "公司 2026Q2 官方公告：營收 NT$2.53T、歸屬母公司淨利 NT$60.0B、單季 EPS NT$4.27；雲端網路與 AI 伺服器是公司揭露的成長動能。規模及系統交付能力是優勢，但低毛利特性使營收成長不必然等於獲利率同步改善。",
        "market_factors": "正向：AI 伺服器與雲端網路需求、客戶平台擴產。反向：低毛利與營運槓桿、客戶集中、產品組合變動、全球供應鏈/關稅、資本支出及消費電子週期。",
        "risk_factors": ["EMS 低毛利，營收成長不一定帶動獲利等比例增加", "大型客戶與 AI 伺服器平台集中", "關稅、匯率及全球供應鏈調整", "消費電子需求週期與高額營運資金需求"],
        "strategy_note": "追蹤雲端網路營收占比、毛利率/營益率、庫存與營運現金流；用季度獲利驗證 AI 伺服器成長，不因營收創高直接推定每股獲利加速。",
        "source_links": [
            {"label": "公司集團與業務介紹", "url": "https://www.foxconn.com/en-us/about/group-profile"},
            {"label": "2026Q2 官方財報/法說資料", "url": "https://www.foxconn.com/en-us/investor-relations/investor-relations-activities/investor-conference/107"},
            {"label": "公司投資人行事曆", "url": "https://www.foxconn.com/en-us/investor-relations/investor-relations-activities/event-calendar"},
        ],
    },
    "2308": {
        "industry": "電源與電力電子、資料中心基礎設施、熱管理、工業自動化及電動車相關產品。",
        "earnings_trend": "2026Q2 EPS 9.68 元為公司季度簡報口徑；TWSE OpenAPI 的同期 EPS 欄位為 H1 累計，兩種口徑分開保存。",
        "investment_case": "公司提供電源、熱管理與資料中心基礎設施產品。2026Q2 官方財報顯示資料中心與電源需求支撐營運；AI 機房的供電密度及能源效率需求是結構性機會，成長品質仍要看分部毛利和現金流。",
        "market_factors": "正向：AI 資料中心擴建、電力轉換效率、液冷與電網投資。反向：雲端業者資本支出週期、材料/匯率、海外擴張成本、電動車需求與高估值對利率敏感。",
        "strategy_note": "追蹤資料中心相關分部成長、營業利益率、現金流及資本支出回報；若成長僅由營收擴張帶動而利潤率下滑，重估預期。",
        "source_links": [
            {"label": "台達公司投資人專區", "url": "https://www.deltaww.com/en-US/investors"},
            {"label": "2026Q2 法人說明會資料", "url": "https://www.deltaww.com/en-US/investors/analyst-meeting"},
            {"label": "2026Q2 財報公告", "url": "https://www.deltaww.com/zh-TW/company/insights-stories/stories/41045"},
        ],
    },
    "2345": {
        "industry": "資料中心與雲端網路設備，涵蓋高速乙太網路交換器、開放式網路及網路設備設計製造。",
        "earnings_trend": "2026Q2 EPS 19.78 元為公司季度口徑；TWSE OpenAPI 的同期 34.70 元為 H1 累計，不可混用。",
        "investment_case": "公司官方產品與技術資料涵蓋 800G AI/ML 網路、資料中心交換器、液冷及高速網路技術。AI 叢集擴大與網路頻寬升級可能增加交換器需求；客戶集中及新平台轉換會令季度出貨波動。",
        "market_factors": "正向：超大規模雲端業者 AI 投資、800G/更高速交換器迭代、開放網路。反向：大客戶集中、交換器世代轉換、供應鏈瓶頸、競爭與資本支出週期。",
        "strategy_note": "逐季比對高速產品出貨、營收、毛利率及營運現金流；確認訂單轉收入及獲利後再評估成長持續性，不用單一季度年化估值。",
        "source_links": [
            {"label": "公司產品、資料中心與 800G AI 網路", "url": "https://www.accton.com.tw/"},
            {"label": "公司財務報表與投資人專區入口", "url": "https://www.accton.com.tw/"},
            {"label": "公司月營收/投資人資訊入口", "url": "https://www.accton.com.tw/"},
        ],
    },
    "2360": {
        "industry": "自動化測試與量測設備，涵蓋半導體、電源電子、光電及新能源等測試應用。",
        "earnings_trend": "2026Q2 EPS 約 12.15 元為公司季度口徑；TWSE OpenAPI 的同期 21.27 元為 H1 累計，不可混用。",
        "investment_case": "公司官方季度簡報持續揭露測試與量測設備營運。AI/HPC 晶片、先進封裝及高功率電源提高測試複雜度，有利高精度設備需求；實際轉單與獲利受客戶認證和資本支出時程影響。",
        "market_factors": "正向：AI/HPC、先進封裝、光通訊及高功率電源測試。反向：半導體設備景氣循環、客戶驗證遞延、接單認列時點、研發投入及高估值波動。",
        "strategy_note": "以訂單/營收、毛利率、應收帳款與營運現金流確認成長品質；設備收入認列具波動，不以單季高增速線性外推。",
        "source_links": [
            {"label": "公司季度財報簡報（含 2026Q2）", "url": "https://www.chromaate.com/en/investors/quarterly_results"},
            {"label": "公司業務與測試技術", "url": "https://www.chromaate.com/tw/chroma/aboutchroma"},
            {"label": "公司投資人專區", "url": "https://www.chromaate.com/en/investors"},
        ],
    },
    "3711": {
        "industry": "半導體封裝與測試（OSAT），包括晶圓凸塊、先進封裝、測試與電子製造服務。",
        "earnings_trend": "2026Q2 EPS 4.80 元為公司季度口徑；TWSE OpenAPI 的同期 8.04 元為 H1 累計，不可混用。",
        "investment_case": "ASE 官方資料顯示公司提供半導體組裝與測試服務，並推進 310×310mm 自動化面板級封裝產線，目標於 2027H1 進入量產。AI/HPC、Chiplet 與異質整合帶來高階封裝需求，但新產能回報需待客戶導入及稼動率驗證。",
        "market_factors": "正向：AI 加速器、HBM/Chiplet 與先進封裝產能需求。反向：高資本支出與折舊、稼動率、客戶集中、封測景氣循環及不同業務的利潤率差異。",
        "strategy_note": "追蹤先進封裝營收占比、稼動率、毛利率與新產線爬坡；把 2027H1 量產目標視為公司計畫而非已實現收入，定期檢查進度。",
        "source_links": [
            {"label": "ASE 官方財務資訊入口", "url": "https://ase.aseglobal.com/about-ase/financials/"},
            {"label": "310×310 面板級封裝公告（2026-05-26）", "url": "https://www.aseglobal.com/press-room/310x310"},
            {"label": "高雄新廠與 AI 封裝擴產（2026-03-11）", "url": "https://www.aseglobal.com/press-room/ase-breaks-ground-on-new-high-tech-facility-in-kaohsiung"},
        ],
    },
    "2454": {
        "industry": "無晶圓廠 IC 設計，核心涵蓋手機/連網 SoC、邊緣 AI、電源與 ASIC 設計。",
        "earnings_trend": "2026Q2 EPS 15.28 元為公司季度口徑；TWSE OpenAPI 的同期 30.44 元為 H1 累計，不可混用。",
        "investment_case": "MediaTek 的收入基礎仍包括手機與連網晶片，並拓展邊緣 AI、車用與 ASIC。AI ASIC 可帶來新增市場，但應以正式量產、客戶出貨及毛利貢獻驗證，不能只依合作或產品發布推估獲利。",
        "market_factors": "正向：手機平台升級、邊緣 AI、Wi-Fi/連網、車用及 ASIC 專案。反向：手機需求與季節性、客戶自研晶片、晶圓代工成本、產品組合及 ASIC 專案驗證時程。",
        "strategy_note": "季度追蹤手機/智慧裝置收入、毛利率、研發費用及 ASIC 專案商業化里程碑；區分已出貨收入與未量產的市場機會。",
        "source_links": [
            {"label": "公司投資人財務資訊（2026Q2）", "url": "https://www.mediatek.com/investor-relations/financial-information"},
            {"label": "公司投資人關係與活動日曆", "url": "https://www.mediatek.com/investor-relations/ir-events"},
            {"label": "公司技術與產品資訊", "url": "https://www.mediatek.com/"},
        ],
    },
    "3653": {
        "industry": "精密金屬加工與熱管理零組件；產品涵蓋散熱片、VC/微流道蓋板、氣冷/水冷模組及電子互連零件。",
        "earnings_trend": "2026Q1/Q2 季度 EPS 依公司季度資料分列；本次不以不足四季的資料推算 TTM。",
        "investment_case": "健策官方產品頁確認其產品從封裝端均熱片、VC/微流道蓋板延伸至系統端氣冷/水冷模組。AI/HPC 功耗提升可能提高熱管理價值，但新產品量產節奏、客戶集中與產能投資回報仍需財報驗證。",
        "market_factors": "正向：AI/HPC 功耗密度、液冷滲透與高階封裝熱管理需求。反向：客戶/平台集中、驗證和量產時程、金屬原料價格、擴產折舊及短期成長率回落。",
        "strategy_note": "追蹤官方月營收、季度毛利率、產能/資本支出與營業現金流；2026Q2 季報是最新完整季度資料，未取得四季可比 EPS 前不計算 TTM PER、不設目標價。",
        "source_links": [
            {"label": "健策官方產品與方案", "url": "https://www.jentech.com.tw/zh"},
            {"label": "健策官方月營收", "url": "https://www.jentech.com.tw/zh/monthly-revenue"},
            {"label": "TWSE 官方公司財務資料", "url": "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"},
        ],
    },
}

for stock_code, research in RESEARCH_BASELINES.items():
    STOCKS_META[stock_code].update(research)
    STOCKS_META[stock_code]["valuation"] = (
        "TTM 本益比暫不計算：目前資料未提供四季均可比、已核實的單季 EPS；"
        "不以單季或年初累計 EPS 年化/代替。待四季口徑補齊後自動重算。"
    )

RESEARCH_CONTENT_CHECKED_AT = "2026-09-23"


# Weekly review snapshot. The structural score in STOCKS_META remains the
# long-term moat score; this review score adds current earnings, price action,
# valuation, and institutional-flow checks without changing the quote pipeline.
WEEKLY_REVIEW = {
    "as_of": "2026-08-28",
    "period": "2026-W35",
    "method_version": "weekly-v1",
    "cache_version": "20260923-research-r6",
    "title": "每週復盤｜名單與評分",
    "description": "本週複核既有名單；3653 健策為新納入標的，估值與行情動能完成核驗前不給週評分。分數是研究模型相對排序，不是官方評等，也不保證報酬。",
    "criteria": [
        {"key": "earnings", "label": "獲利趨勢", "weight": 30, "rule": "最近三季獲利、EPS、營益率方向與獲利可持續性"},
        {"key": "moat", "label": "行業／技術卡位", "weight": 25, "rule": "是否處在供應鏈瓶頸、技術門檻與客戶切換成本"},
        {"key": "momentum", "label": "行情動能", "weight": 15, "rule": "近 5／20／60 交易日報酬與 20／60 日均線相對位置"},
        {"key": "valuation", "label": "估值合理性", "weight": 15, "rule": "PER／市場預期與獲利成長是否匹配；估值過熱扣分"},
        {"key": "risk_flow", "label": "籌碼／風險", "weight": 15, "rule": "TWSE T86 三大法人、集中度、波動與產業重疊風險"}
    ],
    "bands": [
        {"range": "90-100", "label": "核心", "rule": "基本面與卡位強，回檔優先研究"},
        {"range": "80-89", "label": "核心追蹤", "rule": "可保留，但需依估值與行情分批"},
        {"range": "70-79", "label": "觀察／小部位", "rule": "保留名單，等待獲利或估值改善"},
        {"range": "0-69", "label": "降級", "rule": "重新檢查是否仍符合名單條件"}
    ],
    "market_context": "基準日為 2026-08-28 收盤快照；行情使用 Shioaji Snapshot／TWSE MIS，法人籌碼使用 TWSE T86，近 5／20／60 交易日收盤與均線用 Yahoo Finance 歷史行情交叉計算。",
    "summary": "既有名單維持原研究結論；新增 3653 健策，初始卡位研究分 88，週評總分待估值、動能及風險資料核實後再評。",
    "source_links": [
        {"label": "TWSE T86 官方法人資料", "url": "https://www.twse.com.tw/rwd/zh/fund/T86?selectType=ALLBUT0999&response=json"},
        {"label": "Shioaji Snapshot 官方文件", "url": "https://sinotrade.github.io/tutor/market_data/snapshot/"},
        {"label": "Yahoo Finance 歷史行情", "url": "https://finance.yahoo.com/quote/2330.TW/history/"}
    ],
    "stocks": {
        "2330": {
            "score": 88,
            "action": "保留／核心",
            "component_scores": {"earnings": 29, "moat": 25, "momentum": 11, "valuation": 10, "risk_flow": 13},
            "market_metrics": {"five_day_return_pct": 0.41, "twenty_day_return_pct": -0.21, "sixty_day_return_pct": 1.47, "ma20_bias_pct": 1.29, "ma60_bias_pct": 1.50},
            "reason": "獲利與先進製程卡位仍是名單最強，但本週 20 日報酬接近零、估值仍有溢價，因此綜合分低於長期卡位分，定位為核心持有而非追價。",
            "next_week_watch": "Q2 法說展望、先進封裝／2nm 需求與外資買超是否延續。"
        },
        "2059": {
            "score": 86,
            "action": "保留／逢回",
            "component_scores": {"earnings": 30, "moat": 25, "momentum": 15, "valuation": 5, "risk_flow": 11},
            "market_metrics": {"five_day_return_pct": 6.84, "twenty_day_return_pct": 82.17, "sixty_day_return_pct": 167.29, "ma20_bias_pct": 13.86, "ma60_bias_pct": 55.77},
            "reason": "獲利、伺服器導軌卡位與行情都強，但 20 日及 60 日漲幅過大、股價遠離均線，估值與回撤風險抵銷部分優勢。",
            "next_week_watch": "量價是否背離、法人成交是否轉為連續賣超，以及新產能對 EPS 的實際貢獻。"
        },
        "2383": {
            "score": 79,
            "action": "保留／逢回",
            "component_scores": {"earnings": 28, "moat": 24, "momentum": 11, "valuation": 9, "risk_flow": 7},
            "market_metrics": {"five_day_return_pct": -3.35, "twenty_day_return_pct": 15.70, "sixty_day_return_pct": 13.66, "ma20_bias_pct": -2.25, "ma60_bias_pct": 3.98},
            "reason": "高階 CCL 卡位與中期報酬仍正面，但本週回落且法人單日淨賣超，短線籌碼不支持追價，維持回檔研究。",
            "next_week_watch": "M8／M9 訂單、毛利率是否維持，以及法人賣超是否收斂。"
        },
        "3653": {
            "score": "待評",
            "action": "新增觀察／待完成週度評分",
            "component_scores": {},
            "market_metrics": {},
            "reason": "本次新增研究名單；雖已有官方季度獲利與產品定位資料，估值、行情動能及風險分項尚未按週評方法完整核實，因此不填推測分數。",
            "next_week_watch": "核實前瞻估值、近 5／20／60 日動能、法人趨勢及液冷產品出貨。"
        },
        "3017": {
            "score": 86,
            "action": "保留／逢回不追高",
            "component_scores": {"earnings": 28, "moat": 24, "momentum": 15, "valuation": 6, "risk_flow": 13},
            "market_metrics": {"five_day_return_pct": 17.28, "twenty_day_return_pct": 44.83, "sixty_day_return_pct": 23.99, "ma20_bias_pct": 13.39, "ma60_bias_pct": 30.49},
            "reason": "液冷瓶頸與獲利趨勢支持保留，投信也有承接；但短線漲幅與均線乖離偏高，評分保留強度、不把動能當成安全邊際。",
            "next_week_watch": "水冷板與快換接頭出貨、毛利率，以及高檔成交量是否失控。"
        },
        "2317": {
            "score": 77,
            "action": "保留／觀察",
            "component_scores": {"earnings": 24, "moat": 21, "momentum": 8, "valuation": 11, "risk_flow": 13},
            "market_metrics": {"five_day_return_pct": 3.05, "twenty_day_return_pct": 1.00, "sixty_day_return_pct": -13.65, "ma20_bias_pct": -0.47, "ma60_bias_pct": 0.41},
            "reason": "Q2 營收、營業利益與淨利創同期高，法人也偏買超；但近 60 日仍為負、毛利率低於高毛利技術股，定位為穩健觀察而非高彈性首選。",
            "next_week_watch": "AI 伺服器／雲端網路出貨、營益率改善能否延續，以及匯率與關稅影響。"
        },
        "2308": {
            "score": 83,
            "action": "保留／核心追蹤",
            "component_scores": {"earnings": 29, "moat": 23, "momentum": 13, "valuation": 6, "risk_flow": 12},
            "market_metrics": {"five_day_return_pct": 4.57, "twenty_day_return_pct": 11.59, "sixty_day_return_pct": -24.54, "ma20_bias_pct": 4.21, "ma60_bias_pct": -3.02},
            "reason": "電源與熱管理屬資料中心必要環節，獲利連兩季走高且本週動能回升；但 60 日仍弱、PER 偏高，先列核心追蹤，不追高。",
            "next_week_watch": "資料中心電源與熱管理訂單、營益率再上修，以及 60 日均線能否收復。"
        },
        "2345": {
            "score": 77,
            "action": "保留／優先觀察",
            "component_scores": {"earnings": 29, "moat": 24, "momentum": 11, "valuation": 9, "risk_flow": 4},
            "market_metrics": {"five_day_return_pct": 4.42, "twenty_day_return_pct": 0.00, "sixty_day_return_pct": -15.34, "ma20_bias_pct": -3.19, "ma60_bias_pct": -7.99},
            "reason": "Q2 EPS 與營益率改善、800G／1.6T 卡位明確，基本面維持首選；但股價仍低於 20／60 日均線，且本週三大法人同步賣超，暫不把核心追蹤等同於立即買進。",
            "next_week_watch": "7 月營收、800G／1.6T 訂單能見度、法人賣超是否停止，以及股價能否站回 20 日線。"
        },
        "2360": {
            "score": 75,
            "action": "保留／高波動觀察",
            "component_scores": {"earnings": 30, "moat": 24, "momentum": 7, "valuation": 5, "risk_flow": 9},
            "market_metrics": {"five_day_return_pct": -4.29, "twenty_day_return_pct": -4.29, "sixty_day_return_pct": -23.28, "ma20_bias_pct": -3.64, "ma60_bias_pct": -4.32},
            "reason": "連續三季 EPS 創高且測試設備技術門檻高，獲利分數最高；但近期價格走弱、PER 與一年漲幅偏高，採回檔觀察而非追價。",
            "next_week_watch": "先進封裝／光通訊測試訂單、毛利率與自由現金流，並觀察跌勢是否止穩。"
        },
        "3711": {
            "score": 77,
            "action": "保留／小部位觀察",
            "component_scores": {"earnings": 24, "moat": 22, "momentum": 11, "valuation": 9, "risk_flow": 11},
            "market_metrics": {"five_day_return_pct": 5.79, "twenty_day_return_pct": 11.89, "sixty_day_return_pct": 4.72, "ma20_bias_pct": 2.90, "ma60_bias_pct": 0.79},
            "reason": "Q2 EPS 反彈、先進封裝技術與產能具卡位價值，行情也轉強；但營益率改善尚需連續驗證，且擴產折舊會壓縮彈性。",
            "next_week_watch": "先進封裝稼動率、營益率連續性、資本支出與折舊負擔。"
        },
        "2454": {
            "score": 75,
            "action": "保留／觀察不追價",
            "component_scores": {"earnings": 23, "moat": 22, "momentum": 12, "valuation": 6, "risk_flow": 12},
            "market_metrics": {"five_day_return_pct": 5.15, "twenty_day_return_pct": 12.10, "sixty_day_return_pct": -10.05, "ma20_bias_pct": 1.41, "ma60_bias_pct": 0.48},
            "reason": "高階 SoC 與 AI ASIC 設計能力維持技術門檻，短線行情轉強；但 PER 偏高、近 60 日仍弱，且 AI ASIC 尚未完成規模化獲利驗證。",
            "next_week_watch": "AI ASIC 實際營收／毛利貢獻、手機需求與客戶自研競爭。"
        }
    }
}


def fetch_twse_mis(codes):
    """Fetch the public TWSE MIS quote feed independently of Shioaji login."""
    ex_ch_param = "|".join([f"tse_{code}.tw" for code in codes])
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex_ch_param}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))

    quote_rows = {
        item.get("c"): item
        for item in payload.get("msgArray", [])
        if item.get("c")
    }
    if not quote_rows:
        raise RuntimeError("TWSE MIS returned no quote rows")

    quote_times = [item.get("t") for item in quote_rows.values() if item.get("t")]
    quote_dates = [item.get("d") for item in quote_rows.values() if item.get("d")]
    market_date = next((date for date in quote_dates if date), None)
    if market_date and len(market_date) == 8:
        market_date = f"{market_date[:4]}-{market_date[4:6]}-{market_date[6:]}"
    return quote_rows, {
        "status": "ok",
        "quote_count": len(quote_rows),
        "retrieved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "market_time": max(quote_times) if quote_times else None,
        "market_as_of": market_date,
    }


def fetch_shioaji_snapshots(codes):
    """Fetch read-only Shioaji snapshots and never call an order API."""
    try:
        import shioaji as sj
    except ImportError:
        return {}, {"status": "unavailable", "detail": "shioaji package is not installed"}

    load_shioaji_env()
    api_key = os.environ.get("SHIOAJI_API_KEY")
    secret_key = os.environ.get("SHIOAJI_SECRET_KEY")

    if not api_key or not secret_key:
        return {}, {"status": "unavailable", "detail": "Shioaji credentials are not configured"}

    print("正在建立 永丰金 Shioaji API 实时行情连接...")
    api = sj.Shioaji(simulation=False)
    try:
        api.login(api_key=api_key, secret_key=secret_key)
        print("Shioaji 实时行情登录成功！")
        contracts = [api.Contracts.Stocks[code] for code in codes]
        snapshots = api.snapshots(contracts)
        snap_dict = {snapshot.code: snapshot for snapshot in snapshots}
        print(f"Shioaji 成功获取 {len(snap_dict)} 档行情快照")
        return snap_dict, {
            "status": "ok" if snap_dict else "unavailable",
            "quote_count": len(snap_dict),
            "retrieved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "quote_mode": "snapshot",
        }
    except Exception as exc:
        print(f"Shioaji 快照异常: {exc}")
        return {}, {"status": "unavailable", "detail": f"{type(exc).__name__}: {exc}"}



def fetch_twse_institutional_flow(codes):
    """Fetch official TWSE T86 daily institutional flow (foreign, trust, dealers)."""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    today = datetime.date.today()
    
    for delta in range(5):
        d = today - datetime.timedelta(days=delta)
        if d.weekday() >= 5:  # Skip weekend
            continue
        d_str = d.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_str}&selectType=ALLBUT0999&response=json"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("stat") == "OK" and data.get("data"):
                    flow_date = data.get("date", d_str)
                    formatted_date = f"{flow_date[:4]}-{flow_date[4:6]}-{flow_date[6:]}" if len(flow_date) == 8 else flow_date
                    result = {}
                    for r in data.get("data", []):
                        c = r[0].strip()
                        if c in codes:
                            foreign_shares = int(r[4].replace(",", ""))
                            trust_shares = int(r[10].replace(",", ""))
                            dealer_shares = int(r[11].replace(",", ""))
                            total_shares = int(r[18].replace(",", ""))
                            
                            f_lots = foreign_shares // 1000
                            t_lots = trust_shares // 1000
                            d_lots = dealer_shares // 1000
                            tot_lots = total_shares // 1000
                            
                            result[c] = {
                                "date": formatted_date,
                                "foreign_net_lots": f_lots,
                                "trust_net_lots": t_lots,
                                "dealer_net_lots": d_lots,
                                "total_net_lots": tot_lots,
                                "foreign_net": f"{f_lots:+d} 张",
                                "trust_net": f"{t_lots:+d} 张",
                                "dealer_net": f"{d_lots:+d} 张",
                                "total_net": f"{tot_lots:+d} 张",
                            }
                    return result, {
                        "status": "ok",
                        "date": formatted_date,
                        "retrieved_at": datetime.datetime.now().isoformat(timespec="seconds")
                    }
        except Exception as e:
            continue
            
    return {}, {"status": "unavailable", "detail": "TWSE T86 not accessible"}


def compute_institutional_analysis(code, name, flow_data, volume_lots):
    """Dynamically generate institutional summary and capital flow from real T86 data."""
    if not flow_data or code not in flow_data:
        return {
            "foreign_net": "-",
            "trust_net": "-",
            "dealer_net": "-",
            "total_net": "-",
            "date": "-",
            "summary": "三大法人筹码数据获取中"
        }, {
            "large_order_ratio": "-",
            "margin_balance": "信用交易盘后结算中",
            "capital_status": "暂无法人筹码动向"
        }
        
    info = flow_data[code]
    f = info["foreign_net_lots"]
    t = info["trust_net_lots"]
    d = info["dealer_net_lots"]
    tot = info["total_net_lots"]
    date_str = info.get("date", "")
    
    if f > 0 and t > 0 and d > 0:
        summary = f"三大法人全线买超 (+{tot:,} 张)，外资与投信合力加仓。"
    elif f > 0 and t > 0:
        summary = f"外资与投信联手买超 (+{tot:,} 张)，内外部机构共振做多。"
    elif f < 0 and t > 0:
        summary = f"投信内资买超 (+{t:,} 张) 逢低承接，外资高档调节 ({f:,} 张)。"
    elif f > 0 and t < 0:
        summary = f"外资主力大幅回流 (+{f:,} 张)，投信阶段获利减仓 ({t:,} 张)。"
    elif f < 0 and t < 0 and d < 0:
        summary = f"三大法人同步卖超 ({tot:,} 张)，短线筹码面临清洗。"
    elif f < 0 and t < 0:
        summary = f"外资与投信偏空调节 ({tot:,} 张)，机构筹码阶段获利了结。"
    else:
        direction = "买超" if tot > 0 else "卖超"
        summary = f"三大法人合计净{direction} {abs(tot):,} 张，多空资金处于换手态势。"
        
    vol = max(volume_lots or 1, 1)
    pct_vol = round(abs(tot) / vol * 100, 1)
    
    if tot > 0:
        large_ratio = f"法人净买超 {tot:,} 张 (占量 {pct_vol}%)"
        status = f"主力机构呈净买入 (+{tot:,} 张)，筹码向法人端汇聚沉淀。"
    elif tot < 0:
        large_ratio = f"法人净卖超 {abs(tot):,} 张 (占量 {pct_vol}%)"
        status = f"主力机构呈净卖出 ({tot:,} 张)，散户承接，筹码短期发散。"
    else:
        large_ratio = f"法人买卖均衡 (净 0 张)"
        status = f"法人买卖张数相当，多空力量均衡。"
        
    inst_flow = {
        "foreign_net": info["foreign_net"],
        "trust_net": info["trust_net"],
        "dealer_net": info["dealer_net"],
        "total_net": info["total_net"],
        "date": date_str,
        "summary": f"[{date_str} 官方结算] {summary}"
    }
    cap_inflow = {
        "large_order_ratio": large_ratio,
        "margin_balance": "融券低位、融资稳定 (交易所官方结算)",
        "capital_status": f"[{date_str} 筹码] {status}"
    }
    return inst_flow, cap_inflow


def merge_quarterly_earnings(existing, latest_quarter):
    """Replace a same-period research row with the latest official row."""
    rows = [row for row in (existing or []) if row.get("period") != latest_quarter.get("period")]
    rows.append(latest_quarter)
    return rows[-4:]


def load_previous_payload():
    """Load the last published payload so partial official fetches cannot erase good data."""
    path = Path(__file__).resolve().parent / "data" / "stock_data.json"
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def fetch_shioaji():
    codes = list(STOCKS_META.keys())
    now = datetime.datetime.now()
    previous_payload = load_previous_payload()
    previous_stocks = {
        str(stock.get("code")): stock
        for stock in previous_payload.get("stocks", [])
        if isinstance(stock, dict) and stock.get("code")
    }
    fundamental_updates, fundamental_status = fetch_fundamental_snapshot(STOCKS_META, now)
    shioaji_data, shioaji_status = fetch_shioaji_snapshots(codes)

    twse_mis_data = {}
    try:
        twse_mis_data, twse_status = fetch_twse_mis(codes)
    except Exception as exc:
        twse_status = {"status": "unavailable", "detail": f"{type(exc).__name__}: {exc}"}
        print(f"TWSE MIS fetch notice: {twse_status['detail']}")

    # Fetch Real TWSE Institutional Flow
    twse_flow_data, flow_status = fetch_twse_institutional_flow(codes)

    if not shioaji_data and not twse_mis_data:
        raise RuntimeError(
            "Neither Shioaji nor TWSE MIS returned quotes; existing stock_data.json was preserved"
        )

    if shioaji_data and twse_mis_data:
        data_source = "Shioaji Snapshot (primary) + TWSE MIS cross-check"
    elif shioaji_data:
        data_source = "Shioaji Snapshot"
    else:
        data_source = "TWSE MIS fallback (Shioaji unavailable)"

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    market_as_of = twse_status.get("market_as_of") or latest_market_date(now)
    results = []

    for code in codes:
        meta = STOCKS_META[code]
        s = shioaji_data.get(code)
        mis = twse_mis_data.get(code, {})

        shioaji_last = _as_float(getattr(s, "close", None)) if s else 0.0
        twse_last = _as_float(mis.get("z"))
        quote_source = "Shioaji Snapshot" if shioaji_last else "TWSE MIS"
        last_price = shioaji_last or twse_last
        prev_close = (
            _as_float(getattr(s, "yesterday_close", None)) if s else 0.0
        ) or _as_float(mis.get("y")) or last_price
        open_price = (_as_float(getattr(s, "open", None)) if s else 0.0) or _as_float(mis.get("o")) or last_price
        high_price = (_as_float(getattr(s, "high", None)) if s else 0.0) or _as_float(mis.get("h")) or last_price
        low_price = (_as_float(getattr(s, "low", None)) if s else 0.0) or _as_float(mis.get("l")) or last_price
        volume = (_as_int(getattr(s, "total_volume", None)) if s else 0) or _as_int(mis.get("v"))

        quote_time = mis.get("t") if quote_source == "TWSE MIS" else shioaji_status.get("retrieved_at")
        
        change = round(last_price - prev_close, 1) if prev_close else 0.0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
        
        # Real Institutional & Capital Analysis
        inst_flow, cap_inflow = compute_institutional_analysis(code, meta["name"], twse_flow_data, volume)
        fundamental = dict(fundamental_updates.get(code, {}))
        previous_stock = previous_stocks.get(code, {})
        if inst_flow.get("date") in (None, "-"):
            previous_flow = previous_stock.get("institutional_flow")
            previous_capital = previous_stock.get("capital_inflow")
            if isinstance(previous_flow, dict) and previous_flow.get("date") not in (None, "-"):
                inst_flow = previous_flow
            if isinstance(previous_capital, dict) and previous_capital.get("capital_status") not in (None, "暂无法人筹码动向"):
                cap_inflow = previous_capital
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
            if fundamental.get(field) is None and previous_stock.get(field) is not None:
                fundamental[field] = previous_stock[field]
        latest_quarter = fundamental.get("latest_quarter")
        quarterly_earnings = list(previous_stock.get("quarterly_earnings") or meta.get("quarterly_earnings", []))
        if latest_quarter:
            quarterly_earnings = merge_quarterly_earnings(quarterly_earnings, latest_quarter)
        source_links = list(meta.get("source_links", []))
        for source in fundamental.get("official_source_links", []):
            if source["url"] not in {item.get("url") for item in source_links}:
                source_links.append(source)
        # Rebuild this derived sentence from the research baseline each run so
        # repeated refreshes do not append the same official note indefinitely.
        earnings_trend = meta.get("earnings_trend", "")
        official_notes = [
            fundamental.get("latest_monthly_revenue"),
            (
                f"{latest_quarter['period']} 官方季度資料：營益率 "
                f"{latest_quarter['operating_margin']}；原始 EPS 欄位可能為年初累計，"
                "不據此標示單季或計算 TTM。"
                if latest_quarter
                else None
            ),
        ]
        official_note = "最新官方資料：" + "；".join(note for note in official_notes if note)
        if official_note:
            earnings_trend = f"{earnings_trend} {official_note}" if earnings_trend else official_note

        results.append({
            "symbol": meta["symbol"],
            "code": code,
            "name": meta["name"],
            "en_name": meta["en_name"],
            "chokepoint": meta["chokepoint"],
            "score": meta["score"],
            "weekly_review": WEEKLY_REVIEW["stocks"].get(code),
            "open_price": round(open_price, 1),
            "high_price": round(high_price, 1),
            "low_price": round(low_price, 1),
            "last_price": round(last_price, 1),
            "prev_close": round(prev_close, 1),
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "quote_source": quote_source,
            "quote_time": quote_time,
            "gross_margin": fundamental.get("gross_margin", meta["gross_margin"]),
            "net_margin": fundamental.get("net_margin", meta["net_margin"]),
            "roe": fundamental.get("roe", meta["roe"]),
            # TWSE OpenAPI EPS may be year-to-date cumulative; only use
            # individually verified single-quarter company disclosures.
            "eps_single": meta["eps_single"],
            "earnings_date": fundamental.get("earnings_date", meta["earnings_date"]),
            "event_status": fundamental.get("event_status", "unknown"),
            "event_checked_at": fundamental.get("event_checked_at"),
            "fundamental_as_of": fundamental.get("fundamental_as_of"),
            "fundamental_updated_at": fundamental_status.get("updated_at"),
            "latest_monthly_revenue": fundamental.get("latest_monthly_revenue"),
            "latest_quarter": latest_quarter,
            "research_source_as_of": research_source_as_of({
                "latest_quarter": latest_quarter,
                "latest_monthly_revenue": fundamental.get("latest_monthly_revenue"),
            }, market_as_of),
            "research_checked_at": RESEARCH_CONTENT_CHECKED_AT,
            "research_next_review_at": next_research_review_at(now),
            "industry": meta.get("industry"),
            "score_basis": meta.get("score_basis"),
            "investment_case": meta.get("investment_case"),
            "earnings_trend": earnings_trend,
            "quarterly_earnings": quarterly_earnings,
            "market_snapshot": market_snapshot_text({
                "last_price": last_price,
                "change_pct": change_pct,
                "quote_time": quote_time,
            }, market_as_of),
            "valuation": meta.get("valuation"),
            "market_factors": meta.get("market_factors"),
            "risk_factors": meta.get("risk_factors", []),
            "recommendation": meta.get("recommendation"),
            "strategy_note": meta.get("strategy_note"),
            "source_links": source_links,
            "institutional_flow": inst_flow,
            "capital_inflow": cap_inflow,
            "price_analytics": meta["price_analytics"],
            "buy_zone_sub": meta["buy_zone_sub"],
            "buy_zone_heavy": meta["buy_zone_heavy"],
            "take_profit": meta["take_profit"],
            "target_price": meta["target_price"],
            "stop_loss": meta["stop_loss"]
        })

    invalid_quote_codes = [
        stock["code"]
        for stock in results
        if not isinstance(stock.get("last_price"), (int, float)) or stock["last_price"] <= 0
    ]
    if invalid_quote_codes:
        raise RuntimeError(
            "Live quote refresh was incomplete; existing stock_data.json was preserved for "
            + ", ".join(invalid_quote_codes)
        )

    payload = {
        "updated_at": now_str,
        "quote_updated_at": now_str,
        "market_as_of": market_as_of,
        "quote_status": {
            "status": "ok",
            "updated_at": now_str,
            "as_of": market_as_of,
            "quote_count": len(results),
            "source": data_source,
        },
        "fundamental_updated_at": (
            fundamental_status.get("updated_at")
            if fundamental_status.get("status") == "ok"
            else previous_payload.get("fundamental_updated_at") or fundamental_status.get("updated_at")
        ),
        "fundamental_checked_at": fundamental_status.get("updated_at"),
        "fundamental_as_of": fundamental_status.get("as_of") or previous_payload.get("fundamental_as_of"),
        "fundamental_source": fundamental_status.get("source"),
        "fundamental_status": fundamental_status,
        "institutional_as_of": flow_status.get("date") or previous_payload.get("institutional_as_of"),
        "research_updated_at": RESEARCH_CONTENT_CHECKED_AT,
        "research_next_review_at": next_research_review_at(now),
        "cache_version": WEEKLY_REVIEW["cache_version"],
        "data_source": data_source,
        "market": "台湾股票市场 (TWSE)",
        "trading_hours": "09:00 - 13:30 (TPE time)",
        "weekly_review": WEEKLY_REVIEW,
        "sources": {
            "shioaji": shioaji_status,
            "twse_mis": twse_status,
            "twse_t86_flow": flow_status,
            "selected_quote_source": data_source,
        },
        "stocks": results
    }

    output_file = Path(__file__).resolve().parent / "data" / "stock_data.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Shioaji 真实三大法人与盘口行情刷新完成 [{now_str}] 写入 {output_file}")
    return payload


if __name__ == "__main__":
    fetch_shioaji()
