# MEMORY.md - 台湾股市分析 Dashboard 架构决策与记忆归档

## 1. 项目核心决策 (Architecture Decision Records)
- **Active Workspace 路径**: `/Users/TonyFu/.gemini/antigravity/scratch/taiwan-stock-dashboard`
- **公网 Pages 链接**: `https://tonytcfu.github.io/taiwan-stock-analysis/` (公网标签: **台湾股市分析**)
- **iCloud 桌面文件路径**: `/Users/TonyFu/Desktop/台湾股市分析/台股 5 大 AI 核心卡位龙头深度投资与买卖点筹码量化分析表.xlsx`
- **数据源**: 永丰金 Shioaji API (直连 TWSE 交易所实时盘口，关联账户 `H121527648` / `傅天君`)。
- **凭证加载规范**: 本地优先读取 `/Users/TonyFu/Documents/台股量化Antigravity/.shioaji.local.env`，遵守 R.A.I.L.G.U.A.R.D 规范，明文密钥决不上传 Git / 公网。
- **防缓存机制**: `index.html` 包含 `Cache-Control: no-cache` 标头，数据读取采用 `data/stock_data.json?v=TIMESTAMP` 强制刷刷新。
- **本地服务状态**: 本地 HTTP 预览服务（端口 8899）已应用户要求主动终止（`task-79` killed），完全依赖公网 Pages URL 跨端调阅。

## 2. 核心股票池与 Serenity 卡位数据
1. **台积电 (2330.TW)**: 晶圆代工/CoWoS 垄断 (98分) | 毛利 65-67% | 法人: 外资+2,450张
2. **川湖 (2059.TW)**: AI 机柜精密导轨 (92分) | 毛利 87% | 法人: 投信+120张 (筹码集中度 82%)
3. **台光电 (2383.TW)**: M8/M9 高阶 CCL 材料 (88分) | 毛利 33.8% | 法人: 三大法人买超 (+2,080张)
4. **奇鋐 (3017.TW)**: 液冷/水冷系统龙头 (85分) | 毛利 33.8-35% | 法人: 投信暴买 +1,450张
5. **鸿海 (2317.TW)**: NVL72/GB200 超级机柜集成 (81分) | 毛利 6.2-6.8% | 法人: 三大法人狂买 (+16,300张)

## 3. 运维指令
- 运行公网推流脚本: `python3 sync_and_push.py`
- 详细总结报告文件: `REPORTS/20260812_taiwan_stock_deep_dive.md`
