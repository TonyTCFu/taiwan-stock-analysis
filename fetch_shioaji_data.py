import os
import json
import datetime
from pathlib import Path
import shioaji as sj

# Load Shioaji credentials from local env file or environment
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
        "buy_zone_sub": "2,200 - 2,300 元",
        "buy_zone_heavy": "2,050 - 2,150 元",
        "take_profit": "2,750 - 2,900 元",
        "target_price": "3,200 - 3,500 元",
        "stop_loss": "1,980 元",
        "chips_summary": "外资持股 74%+ 主导控盘，日成交 1.5万-1.8万张；高档震荡调节，投信逢低吸纳，筹码极沉稳。"
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
        "buy_zone_sub": "11,000 - 11,800 元",
        "buy_zone_heavy": "9,800 - 10,500 元",
        "take_profit": "14,500 - 15,500 元",
        "target_price": "17,000 - 17,500 元",
        "stop_loss": "9,200 元",
        "chips_summary": "股本仅 9.5 亿，高单价低流动性，日成交仅数百至千张；投信与内资主力锁筹极紧，毛利87%易轧空。"
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
        "buy_zone_sub": "3,950 - 4,200 元",
        "buy_zone_heavy": "3,600 - 3,800 元",
        "take_profit": "4,900 - 5,200 元",
        "target_price": "5,600 - 5,900 元",
        "stop_loss": "3,450 元",
        "chips_summary": "法人双向作多（外资+投信连续买超），日成交 3,000-6,000 张；高阶材料放量，换手结构健康。"
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
        "buy_zone_sub": "2,450 - 2,600 元",
        "buy_zone_heavy": "2,250 - 2,380 元",
        "take_profit": "3,100 - 3,300 元",
        "target_price": "3,700 - 4,000 元",
        "stop_loss": "2,100 元",
        "chips_summary": "人气交易标的，单日成交 8,000-15,000 张；外资短线洗盘，投信低位连续吸筹，水冷放量强撑。"
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
        "buy_zone_sub": "255 - 270 元",
        "buy_zone_heavy": "238 - 248 元",
        "take_profit": "315 - 335 元",
        "target_price": "360 - 380 元",
        "stop_loss": "225 元",
        "chips_summary": "大盘权重与流动性极佳资产，单日成交 5万-10万张；外资与内资巨额资金流向重回，AI 占比洗刷买盘。"
    }
}

def fetch_shioaji():
    load_shioaji_env()
    api_key = os.environ.get("SHIOAJI_API_KEY")
    secret_key = os.environ.get("SHIOAJI_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError("SHIOAJI_API_KEY / SHIOAJI_SECRET_KEY 未能找到！请检查 .shioaji.local.env 配置")

    print(f"正在建立 永丰金 Shioaji API 实时行情连接...")
    api = sj.Shioaji(simulation=False)
    api.login(api_key=api_key, secret_key=secret_key)
    print("Shioaji 实时行情登录成功！")

    codes = list(STOCKS_META.keys())
    contracts = [api.Contracts.Stocks[code] for code in codes]
    snapshots = api.snapshots(contracts)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    for s in snapshots:
        code = s.code
        meta = STOCKS_META[code]
        
        open_price = float(s.open) if s.open else 0.0
        high_price = float(s.high) if s.high else 0.0
        low_price = float(s.low) if s.low else 0.0
        close_price = float(s.close) if s.close else 0.0
        volume = int(s.total_volume) if s.total_volume else 0
        
        # Calculate daily change if open/close present
        change = round(close_price - open_price, 1) if open_price else 0.0
        change_pct = round((change / open_price) * 100, 2) if open_price else 0.0
        
        results.append({
            "symbol": meta["symbol"],
            "code": code,
            "name": meta["name"],
            "en_name": meta["en_name"],
            "chokepoint": meta["chokepoint"],
            "score": meta["score"],
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "last_price": close_price,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "gross_margin": meta["gross_margin"],
            "net_margin": meta["net_margin"],
            "roe": meta["roe"],
            "eps_single": meta["eps_single"],
            "buy_zone_sub": meta["buy_zone_sub"],
            "buy_zone_heavy": meta["buy_zone_heavy"],
            "take_profit": meta["take_profit"],
            "target_price": meta["target_price"],
            "stop_loss": meta["stop_loss"],
            "chips_summary": meta["chips_summary"]
        })

    payload = {
        "updated_at": now_str,
        "data_source": "永丰金 Shioaji API (台湾证券交易所 TWSE 实时行情)",
        "market": "台湾股票市场 (TWSE)",
        "stocks": results
    }

    output_file = Path(__file__).resolve().parent / "data" / "stock_data.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Shioaji 实时数据刷新完成 [{now_str}] 写入 {output_file}")
    return payload

if __name__ == "__main__":
    fetch_shioaji()
