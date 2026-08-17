# HANDOVER.md - 台湾股市分析项目全量项目交接与运维指南 (Handover Document)

> **交接背景**: 本项目已将对话框 `@[conversation:"台湾优质潜力股分析"]`（Conversation ID: `236b9bdf-d399-4da3-8f7f-3f6b26ffcc9f`）中的所有对话内容、分析成果、Serenity 估值模型、买卖点量化策略、Shioaji 交易所接口集成、iCloud 桌面 Excel 绘图及 Web Dashboard 自动化部署全量迁移并整合至当前工作区项目 `/Users/TonyFu/Desktop/台湾股市分析` 中。

---

## 一、 项目概览与关键入口 (Key Access Points)

| 项目要素 | 详细信息 / 路径 |
| :--- | :--- |
| **项目工作区 (Active Workspace)** | `/Users/TonyFu/Desktop/台湾股市分析` |
| **公网 Web Dashboard 调阅地址** | [https://tonytcfu.github.io/taiwan-stock-analysis/](https://tonytcfu.github.io/taiwan-stock-analysis/) *(标签/名称: **台股龍頭股**)* |
| **iCloud 桌面量化分析 Excel** | `/Users/TonyFu/Desktop/台湾股市分析/台股 5 大 AI 核心卡位龙头深度投资与买卖点筹码量化分析表.xlsx` |
| **完整深度分析总结报告** | `/Users/TonyFu/Desktop/台湾股市分析/REPORTS/20260812_taiwan_stock_deep_dive.md` |
| **数据源接口** | 永丰金 Shioaji Python SDK (直连 TWSE/TPEx 交易所实时盘口与三大法人筹码，关联账户 `H121527648` / `傅天君`) |
| **安全密钥配置文件** | `/Users/TonyFu/Documents/台股量化Antigravity/.shioaji.local.env` |

---

## 二、 对话框迁移的核心内容汇总 (Migrated Core Contents)

### 1. 技能盘点与分析方法论 (Skills & Methodology)
对话中成功盘点并调用了以下专业技能：
- `serenity-hunter` (瓶颈猎手): 沿 AI 产业链逆向拆解（下游 -> 中游器件 -> 最上游衬底/材料），挖掘切换时间 $>12$ 个月的“铲子卖家”。
- `serenity-analyst` (九步估值与风控): 执行卡点打分、3 级证据阶梯及 8 个罚分因子扫描。
- `shioaji-taiwan-stock` (永丰金实时盘口与筹码): 实时读取台股开/收盘、高低价、Tick 与外资/投信/自营商买卖超。

### 2. 台股 5 大 AI 核心卡位龙头全景数据

| 代码 | 公司名称 | Serenity 卡位定位 | 评分 | 毛利率 / ROE | 三大法人筹码状态 | 建议买入位 | 波段止盈位 | 长线目标价 | 止损价 | 财报公布日 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2330** | **台积电** | CoWoS/2nm/3nm代工垄断 | **98分** | 66.0% / 40.5% | 外资买超 +2,450 张 (持股 74.2%) | 2,200 - 2,300 | 2,750 - 2,900 | 3,200 - 3,500 | 1,980 | 2026-10-15 (法说) |
| **2059** | **川湖** | AI 服务器超级机柜导轨 | **92分** | 87.0% / 21.7% | 投信买超 +120 张 (筹码集中度 82%) | 11,000 - 11,800 | 14,500 - 15,500 | 17,000 - 17,500 | 9,200 | 2026-11-06 (财报) |
| **2383** | **台光电** | 800G/1.6T M8/M9 高阶 CCL | **88分** | 33.8% / 18.6% | 三大法人全买超 (+2,080 张) | 3,950 - 4,200 | 4,900 - 5,200 | 5,600 - 5,900 | 3,450 | 2026-10-29 (财报) |
| **3017** | **奇鋐** | AI 服务器水冷/液冷系统 | **85分** | 33.8% / 17.0% | 投信大买 +1,450 张，散户洗净 | 2,450 - 2,600 | 3,100 - 3,300 | 3,700 - 4,000 | 2,100 | 2026-11-10 (法说) |
| **2317** | **鸿海** | NVL72/GB200 机柜集成 | **81分** | 6.2% / 11.3% | 三大法人暴买 +16,300 张 | 255 - 270 | 315 - 335 | 360 - 380 | 225 | 2026-08-14 (法说) |

---

## 三、 代码资产与文件功能交接 (Codebase Inventory)

1. **`fetch_shioaji_data.py`**:
   - 依赖 `shioaji` Python SDK，自动读取本地环境 `.shioaji.local.env`。
   - 抓取 TWSE/TPEx 盘口实时报价、当日高低价、开盘价、收盘价及三大法人进出张数，写入 `data/stock_data.json`。
2. **`create_shioaji_excel.py`**:
   - 依赖 `openpyxl` 库，读取 `data/stock_data.json` 数据。
   - 自动化绘制美化版 Excel 研报，设置微软雅黑与 Calibri 字体、定制列宽行高与色阶，输出至桌面 `台股 5 大 AI 核心卡位龙头深度投资与买卖点筹码量化分析表.xlsx`。
3. **`sync_and_push.py`**:
   - 连贯同步管道：调用 `fetch_shioaji_data.py` $\rightarrow$ 调用 `create_shioaji_excel.py` $\rightarrow$ `git add .` & `git commit`（生成版本号如 `v20260812_133552`） $\rightarrow$ `git push origin main` 推送到 GitHub Pages。
4. **`dashboard_server.py`**:
   - 本机 Dashboard 刷新桥接服务；`POST /api/refresh` 会实际调用只读 Shioaji snapshot，并独立抓取 TWSE MIS 进行交叉核对。
5. **`index.html`**:
   - Modern Dark Glassmorphism 响应式 Web 仪表盘。
   - 包含多 Tab 分页（核心龙头概览、Serenity 卡位评估、买卖策略矩阵、三大法人筹码、财报公布日预告）。
6. **`AGENTS.md` & `MEMORY.md`**:
   - 记录项目编码标准、技能集成规范、安全约束与架构决策。
7. **`REPORTS/20260812_taiwan_stock_deep_dive.md`**:
   - 归档对话框全部深度研究细节的完整 Markdown 报告。

---

## 四、 运维与日常使用指南 (Operations Manual)

### 1. 每日盘后一键更新行情与推送至公网
在终端中执行以下命令（推荐在 `Active Workspace` 路径下）：
```bash
python3 /Users/TonyFu/Desktop/台湾股市分析/sync_and_push.py
```
> **自动效果**: 
> 1. 自动连接永丰金 Shioaji 抓取最新成交价与筹码；
> 2. 自动更新 iCloud 桌面 Excel；
> 3. 自动打包提交 Git 并推送到公网 Pages。

### 2. 本机 Dashboard 实时刷新

GitHub Pages 只能读取已经发布的静态 JSON，浏览器不能直接执行 Python 或读取本机 Shioaji 凭证。要让 Dashboard 的“强制刷新行情”真正抓取行情，先在项目目录启动本机桥接服务：

```bash
python3 dashboard_server.py
```

然后打开 `http://127.0.0.1:8765/`。按钮会调用本机 `POST /api/refresh`：Shioaji snapshot 为主源，TWSE MIS 独立作为交叉核对/降级源；页面会分别显示两者是否成功。公网 URL 上的按钮只能重载已发布数据，并会明确提示这一限制。

### 3. 单独重新生成 iCloud 桌面 Excel
```bash
python3 /Users/TonyFu/Desktop/台湾股市分析/create_shioaji_excel.py
```

### 4. 多端调阅公网 Dashboard
在 iPhone、iPad、Mac 或任意浏览器打开：
`https://tonytcfu.github.io/taiwan-stock-analysis/`

---

## 五、 风控提示与后续扩展建议

1. **财务预告日跟踪**: 鸿海即将在 2026-08-14（本周五）举办法说会，建议关注其 GB200 出货量及毛利率指导。
2. **凭证保护**: `.shioaji.local.env` 严禁提交至 Git 仓库，维持本地加载模式。
3. **扩展标的池**: 如需新增台股标的（如散热双雄双鸿 3324 或 CCL 龙头台燿 6274），只需修改 `fetch_shioaji_data.py` 中的 `STOCK_LIST` 字典即可。
