# MEMORY.md - 台湾股市分析项目架构决策与记忆归档

## 1. 项目核心决策 (Architecture Decision Records)
- **Active Workspace 路径**: `/Users/TonyFu/Desktop/台湾股市分析`
- **公网 Dashboard URL**: `https://tonytcfu.github.io/taiwan-stock-analysis/` (页面标签/名称: **台股龍頭股**)
- **iCloud 桌面 Excel 路径**: `/Users/TonyFu/Desktop/台湾股市分析/台股 5 大 AI 核心卡位龙头深度投资与买卖点筹码量化分析表.xlsx`
- **数据源与接口**: 永丰金 Shioaji Python SDK (直连 TWSE/TPEx 交易所实时盘口与三大法人筹码，关联账户 `H121527648` / `傅天君`)。
- **凭证加载与安全**: 本地读取凭证文件 `/Users/TonyFu/Documents/台股量化Antigravity/.shioaji.local.env`，遵循 R.A.I.L.G.U.A.R.D 规范，任何明文 Key 严禁提交至版本控制或公网。
- **防缓存与前端加载**: `index.html` 配置 HTTP header `Cache-Control: no-cache`，Ajax 请求拼附 `v=TIMESTAMP` 时间戳强制获取最新数据。
- **实时刷新边界**: GitHub Pages 页面通过公网 Render 行情网关 `https://futienchun-com-dashboard.onrender.com/api/live-quotes` 执行刷新；网关服务端只读调用 Shioaji snapshot，并独立抓取 TWSE MIS 交叉核对/降级，凭证只存在 Render 环境变量，不进入浏览器或仓库。本机 `dashboard_server.py` 仅作为开发/故障排查桥接服务。
- **服务部署状态**: 公网按钮必须走 Render 行情网关，不能依赖用户设备上的 Python、Shioaji 或本地文件；前端在公网网关失败时明确报错，不静默伪装成刷新成功。

## 2. 台股 5 大 AI 核心卡位龙头 Serenity 评估库

| 代码 | 名称 | 卡位定位与核心壁垒 | Serenity 得分 | 获利率 (毛利/净利/ROE) | 三大法人筹码与资金流 | 财报/法说预告日 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2330** | **台积电** | 晶圆代工霸主/CoWoS/2nm垄断 | **98 分** (Strong Buy) | 毛利 65-67% \| 净利 >43% \| ROE 40.5% | 外资持股 74.2%，单日买超 +2,450 张 | **2026-10-15** (26Q3 法说) |
| **2059** | **川湖** | AI 服务器超级机柜导轨独霸 | **92 分** (Strong Buy) | 毛利 87.0% \| 净利 >52% \| ROE 21.7% | 投信买超 +120 张，筹码集中度 82% | **2026-11-06** (26Q3 财报) |
| **2383** | **台光电** | 800G/1.6T CCL 高阶材料 (M8/M9) | **88 分** (Strong Buy) | 毛利 33.8% \| 净利 ~19.5% \| ROE 18.6% | 三大法人全线买超 (+2,080 张) | **2026-10-29** (26Q3 财报) |
| **3017** | **奇鋐** | AI 服务器水冷/液冷系统级霸主 | **85 分** (Strong Buy) | 毛利 33.8-35% \| 净利 ~14.2% \| ROE 17.0% | 投信大举买超 +1,450 张，散户洗筹洗净 | **2026-11-10** (26Q3 法说) |
| **2317** | **鸿海** | NVL72/GB200 整体机柜集成交付 | **81 分** (Strong Buy) | 毛利 6.2-6.8% \| 净利 ~2.8% \| ROE 11.3% | 三大法人暴买 +1.63 万张 (主力占 74.8%) | **2026-08-14** (26Q2 法说) |

## 3. 买卖点量化策略矩阵

- **台积电 (2330.TW)**: 建议买入 2,200 - 2,300 元 \| 强支撑黄金买位 2,050 - 2,150 元 \| 波段止盈 2,750 - 2,900 元 \| 长线目标 3,200 - 3,500 元 \| 止损 1,980 元
- **川湖 (2059.TW)**: 建议买入 11,000 - 11,800 元 \| 强支撑黄金买位 9,800 - 10,500 元 \| 波段止盈 14,500 - 15,500 元 \| 长线目标 17,000 - 17,500 元 \| 止损 9,200 元
- **台光电 (2383.TW)**: 建议买入 3,950 - 4,200 元 \| 强支撑黄金买位 3,600 - 3,800 元 \| 波段止盈 4,900 - 5,200 元 \| 长线目标 5,600 - 5,900 元 \| 止损 3,450 元
- **奇鋐 (3017.TW)**: 建议买入 2,450 - 2,600 元 \| 强支撑黄金买位 2,250 - 2,380 元 \| 波段止盈 3,100 - 3,300 元 \| 长线目标 3,700 - 4,000 元 \| 止损 2,100 元
- **鸿海 (2317.TW)**: 建议买入 255 - 270 元 \| 强支撑黄金买位 238 - 248 元 \| 波段止盈 315 - 335 元 \| 长线目标 360 - 380 元 \| 止损 225 元

## 4. 关键项目文件结构
```
/Users/TonyFu/Desktop/台湾股市分析/
├── AGENTS.md                          # 项目开发与编码规范
├── MEMORY.md                          # 本架构决策与记忆文档
├── HANDOVER.md                        # 全量项目交接与运维指南
├── REPORTS/
│   └── 20260812_taiwan_stock_deep_dive.md # 5 大 AI 核心龙头深度研究报告
├── data/
│   └── stock_data.json                # Shioaji API 实时行情与三大法人 JSON 缓存
├── index.html                         # 响应式 Web Dashboard 静态页面
├── fetch_shioaji_data.py              # Shioaji SDK 盘口与筹码抓取核心脚本
├── dashboard_server.py                # 本机 Dashboard -> Shioaji/TWSE 刷新桥接服务
├── create_shioaji_excel.py             # Openpyxl 绘制 iCloud 桌面美化 Excel 脚本
├── sync_and_push.py                   # 自动定盘、更新版本号并 Push 到 GitHub Pages 脚本
└── deploy_to_github.sh                # GitHub 部署自动化脚本
```

## 5. 运维常用指令
- **一键更新盘口并自动推送到公网 Pages**:
  `python3 sync_and_push.py`
- **查看深度研究报告**:
  `cat REPORTS/20260812_taiwan_stock_deep_dive.md`
