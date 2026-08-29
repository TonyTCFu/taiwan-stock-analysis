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

## 二、 2026-08-17 公网实时行情改造交接（必须阅读）

### 1. 问题、根因与已完成方案

**原问题**：公网 GitHub Pages 的“强制刷新行情”按钮只能重新载入静态 `data/stock_data.json`，无法在用户的 iPhone、iPad、其他电脑或公网浏览器中执行 Python / Shioaji，因此看似刷新、实际没有请求实时行情。

**根因**：GitHub Pages 是静态托管，浏览器既不能运行 Python，也不能安全持有 Shioaji 凭证。把按钮绑定到本机 `dashboard_server.py` 只会在本机有效，不能满足多设备使用。

**现行架构**：

```text
任意设备的 GitHub Pages Dashboard
  └─ 点击“强制刷新行情”
      └─ POST Render /api/live-quotes
          ├─ Shioaji Snapshot（主源，10 檔標的）
          └─ TWSE MIS（独立交叉核对；Shioaji 不可用时降级）
      └─ 浏览器仅更新当前页面的实时行情字段与状态，不接触凭证
```

### 2. 公网服务与凭证边界

| 项目 | 已确认状态 |
| :--- | :--- |
| Dashboard 前端 | `TonyTCFu/taiwan-stock-analysis` 的 GitHub Pages |
| 行情网关 | `https://futienchun-com-dashboard.onrender.com/api/live-quotes` |
| Render 服务 ID | `srv-d8onljk8aovs7385cqo0` |
| Render 后端仓库 | `TonyTCFu/futienchun-com-dashboard`，分支 `main` |
| Shioaji 凭证 | 仅存在 Render Environment 的 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY`；严禁写入仓库、前端、日志、Markdown 或聊天记录 |
| GitHub Secrets | 不会自动同步到 Render；Render 必须单独配置两个变量 |
| 行情权限 | 仅 `api.login`、合约读取、`api.snapshots`、`api.logout`；不调用下单、改单、查持仓或资金 API |

本机 `/usr/bin/python3` 已安装 `shioaji 1.7.2` 并完成真实只读登录与 10/10 Snapshot 验证；这是开发验证，不是公网按钮的运行依赖。

### 3. 代码与部署记录

**GitHub Pages 仓库 `TonyTCFu/taiwan-stock-analysis`**：

| 提交 | 作用 |
| :--- | :--- |
| `10bf39d` | 前端按钮改为调用公网 Render 行情网关；状态区显示 Shioaji / TWSE 两路结果 |
| `47d5e76` | 新增 2308、2345、2360、3711、2454 五檔研究资料、卡片及研究面板；保留既有分頁与刷新流程 |
| `f44a4e0` | 发布 10 檔完整行情 JSON 与 Excel；前端在实时网关返回不完整数据时拒绝半刷新 |
| `0b95e07` | 新增每週復盤資料結構、五項評分規則與 Dashboard 复盘面板 |
| `1f75aa7` | 发布 2026-08-28 最新 10 檔行情、週評分與 `20260828-weekly-r1` 缓存版本 |
| `2026-08-29 本輪分頁調整` | 將完整每週復盤面板移入第五個 Dashboard 分頁，保留既有四個分頁與刷新邏輯，快取版本提升為 `20260829-weekly-tab-r1` |
| `2cdc101` | 推送本机 Shioaji 真实快照与公网架构说明 |
| `0e6db56`、`e5c19ad` | 更新本交接和记忆文档的公网验收基线 |

**Render 后端仓库 `TonyTCFu/futienchun-com-dashboard`**：

| 提交 | 作用 |
| :--- | :--- |
| `df49bb7` | 新增 `scripts/live_quotes.py` 与 `POST /api/live-quotes`，加入 CORS 白名单和刷新冷却 |
| `0c7c3d1` | 修复 Render Python 3.14 访问 TWSE MIS 时的 `Missing Subject Key Identifier`；仍保留 TLS 证书校验，只移除 `VERIFY_X509_STRICT` 兼容性标志 |
| `084b823` | 所有实时响应时间改为 `Asia/Taipei`，避免 Render UTC 时间在页面显示错误 |
| `9b540a1` | Render 行情网关扩展为 10 檔，优先读取已发布的 10 檔基礎資料并拒绝不完整 payload |

后端的关键文件为：

- `scripts/live_quotes.py`：只读 Shioaji Snapshot + TWSE MIS 行情聚合。
- `scripts/serve_dashboard.py`：`/api/live-quotes`、CORS、30 秒全局冷却与既有静态站服务。
- `render.yaml`：声明 Render 所需变量名与允许来源；不包含变量值。

### 4. 最终公网验收（已通过）

2026-08-28 以真实浏览器打开 `https://tonytcfu.github.io/taiwan-stock-analysis/`，实际点击“🔄 强制刷新行情”后，页面从静态状态切换为：

- `Shioaji 已连接 · TWSE 已更新`
- 10/10 Shioaji Snapshot 成功
- 10/10 TWSE MIS 成功
- 公网 `POST /api/live-quotes` 返回 HTTP 200 与允许 GitHub Pages 的 CORS 来源
- 页面显示的台湾时间为 `2026-08-28 21:04:27`，不再误用 Render UTC
- 页面显示缓存版本 `v20260828-weekly-r1`，并渲染每週復盤日期、评分规则、5 项拆分分数与 10 檔逐檔理由
- 核心卡片、三大法人、财报、买卖策略四个分頁均显示 10 檔；浏览器 console 无错误或警告
- 390px 移动端复盘区、卡片与分頁无横向溢出（`scrollWidth = 390`）

### 4.1 每週復盤資料契約（2026-08-28）

Dashboard 的 `weekly_review` 以 `2026-W35` 为基准，评分权重固定为：获利趋势 30、行业／技术卡位 25、行情动能 15、估值合理性 15、筹码／风险 15。分级为 90-100 核心、80-89 核心追踪、70-79 观察／小部位、0-69 降级。

本週分數：`2330:88`、`2059:86`、`2383:79`、`3017:86`、`2317:77`、`2308:83`、`2345:77`、`2360:75`、`3711:77`、`2454:75`。每檔資料包含五項拆分分数、近 5／20／60 交易日報酬、20／60 日均線乖離、評分理由與下週觀察事項。行情基準為 Shioaji／TWSE，歷史價格使用 Yahoo Finance 交叉計算；官方來源連結已放在頁面復盤區。

### 5. 使用与故障排查

1. 任意设备只需打开 GitHub Pages，点击“强制刷新行情”；不需要安装 Python、Shioaji 或登入 Render。
2. 连续刷新少于 30 秒会返回 HTTP 429，这是保护 Shioaji 登录/行情流量的设计；等待后重试。
3. 若页面显示 Shioaji 未连接但 TWSE 已更新，先查 Render Environment 是否仍有两个变量名和值；不在浏览器或 GitHub Pages 中配置凭证。
4. 若页面显示 TWSE 未更新，先查 Render `/api/live-quotes` 的响应 `sources.twse_mis.detail`。已知 Python 3.14 证书严格校验问题已由 `0c7c3d1` 修复，若复发不可用 `verify=False` 绕过 TLS。
5. 若 GitHub 推送后 Render 没有自动部署，Render 曾出现 GitHub 部署故障提示；在 Render 服务页选择 `Manual Deploy` → `Deploy latest commit`，然后再做一次公网按钮验收。
6. 截图中出现的 `[rebuild] Dashboard 重建失败` 是既有定时离线模型重建任务，和本实时按钮调用路径独立；它不阻断 `/api/live-quotes`。修复该任务时不得为了消除日志而禁用交易日的模型/模拟盘重建，需单独定位其离线资产缓存问题。

---

## 三、 对话框迁移的核心内容汇总 (Migrated Core Contents)

### 1. 技能盘点与分析方法论 (Skills & Methodology)
对话中成功盘点并调用了以下专业技能：
- `serenity-hunter` (瓶颈猎手): 沿 AI 产业链逆向拆解（下游 -> 中游器件 -> 最上游衬底/材料），挖掘切换时间 $>12$ 个月的“铲子卖家”。
- `serenity-analyst` (九步估值与风控): 执行卡点打分、3 级证据阶梯及 8 个罚分因子扫描。
- `shioaji-taiwan-stock` (永丰金实时盘口与筹码): 实时读取台股开/收盘、高低价、Tick 与外资/投信/自营商买卖超。

### 2. 台股 10 大 AI 核心卡位龙头全景数据

| 代码 | 公司名称 | Serenity 卡位定位 | 评分 | 毛利率 / ROE | 三大法人筹码状态 | 建议买入位 | 波段止盈位 | 长线目标价 | 止损价 | 财报公布日 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2330** | **台积电** | CoWoS/2nm/3nm代工垄断 | **98分** | 66.0% / 40.5% | 外资买超 +2,450 张 (持股 74.2%) | 2,200 - 2,300 | 2,750 - 2,900 | 3,200 - 3,500 | 1,980 | 2026-10-15 (法说) |
| **2059** | **川湖** | AI 服务器超级机柜导轨 | **92分** | 87.0% / 21.7% | 投信买超 +120 张 (筹码集中度 82%) | 11,000 - 11,800 | 14,500 - 15,500 | 17,000 - 17,500 | 9,200 | 2026-11-06 (财报) |
| **2383** | **台光电** | 800G/1.6T M8/M9 高阶 CCL | **88分** | 33.8% / 18.6% | 三大法人全买超 (+2,080 张) | 3,950 - 4,200 | 4,900 - 5,200 | 5,600 - 5,900 | 3,450 | 2026-10-29 (财报) |
| **3017** | **奇鋐** | AI 服务器水冷/液冷系统 | **85分** | 33.8% / 17.0% | 投信大买 +1,450 张，散户洗净 | 2,450 - 2,600 | 3,100 - 3,300 | 3,700 - 4,000 | 2,100 | 2026-11-10 (法说) |
| **2317** | **鸿海** | NVL72/GB200 机柜集成 | **81分** | 6.2% / 11.3% | 三大法人暴买 +16,300 张 | 255 - 270 | 315 - 335 | 360 - 380 | 225 | 2026-08-14 (法说) |
| **2345** | **智邦** | 800G/1.6T AI 高速交换器 | **86分** | 19.7% / 待更新 | Q2 EPS 19.78、營益率約 15.0% | 分批觀察 | 依訂單與 EPS 趨勢 | 不預設固定目標 | 依基本面檢視 | 2026Q2 已公告 |
| **2308** | **台達電** | AI 資料中心電源與熱管理 | **85分** | 35.6% / 待更新 | Q2 EPS 9.68、營益率 16.7% | 分批觀察 | 依獲利與趨勢 | 不預設固定目標 | 依基本面檢視 | 2026Q2 已公告 |
| **2360** | **致茂** | AI/先進封裝高精度測試設備 | **84分** | 約 60.5% / 待更新 | Q2 EPS 約 12.15、營益率約 38.7% | 回檔分批 | 依 EPS 與毛利率 | 不預設固定目標 | 獲利趨勢反轉檢視 | 2026Q2 已公告 |
| **3711** | **日月光投控** | AI 先進封裝與測試 | **79分** | 待更新 / 18.2%年化 | Q2 EPS 4.80、營益率 11.1% | 小部位觀察 | 依封裝稼動率 | 不預設固定目標 | 資本支出/折舊檢視 | 2026Q2 已公告 |
| **2454** | **聯發科** | AI ASIC/邊緣 AI SoC | **77分** | 46.2% / 待更新 | Q2 EPS 15.28、營益率 15.0% | 觀察不追價 | 依 ASIC 營收 | 不預設固定目標 | 獲利/ASIC 時程檢視 | 2026Q2 已公告 |

---

## 四、 代码资产与文件功能交接 (Codebase Inventory)

1. **`fetch_shioaji_data.py`**:
   - 依赖 `shioaji` Python SDK，自动读取本地环境 `.shioaji.local.env`。
   - 抓取 TWSE/TPEx 盘口实时报价、当日高低价、开盘价、收盘价及三大法人进出张数，写入 `data/stock_data.json`。
2. **`create_shioaji_excel.py`**:
   - 依赖 `openpyxl` 库，读取 `data/stock_data.json` 数据。
   - 自动化绘制美化版 Excel 研报，设置微软雅黑与 Calibri 字体、定制列宽行高与色阶，按资料笔数输出当前 10 檔数据；文件名仍保留旧名称以兼容既有路径。
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

## 五、 运维与日常使用指南 (Operations Manual)

### 1. 每日盘后一键更新行情与推送至公网
在终端中执行以下命令（推荐在 `Active Workspace` 路径下）：
```bash
python3 /Users/TonyFu/Desktop/台湾股市分析/sync_and_push.py
```
> **自动效果**: 
> 1. 自动连接永丰金 Shioaji 抓取最新成交价与筹码；
> 2. 自动更新 iCloud 桌面 Excel；
> 3. 自动打包提交 Git 并推送到公网 Pages。

### 2. Dashboard 公网实时刷新

Dashboard 的“强制刷新行情”现在调用公网 Render 行情网关，用户从任何设备打开 GitHub Pages 都能执行，不依赖该设备安装 Python/Shioaji：

`POST https://futienchun-com-dashboard.onrender.com/api/live-quotes`

公网网关服务端读取 Render 的 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY` 环境变量，只执行只读行情请求；Shioaji 为主源，TWSE MIS 独立交叉核对并作为降级源。两者状态会回传到页面并写入响应的 `sources`。

Render 的两个凭证必须在 Render Environment 单独配置，GitHub Actions Secrets 不会自动同步。网关有 30 秒全局冷却，连续点击会收到 429，属于保护机制；响应时间统一使用 Asia/Taipei。2026-08-28 已完成公网验收，Shioaji 与 TWSE MIS 均返回 10/10，并返回 `cache_version=20260828-weekly-r1` 与週評分资料。

### 5.1 2026-08-29 每週復盤分頁調整

每週復盤完整內容不再佔用主頁固定區域，已移入第五個分頁 `📈 每周复盘｜名单与评分`。既有四個分頁（核心行情、法人資金、財報預告、買賣策略）及 `loadStockData(true)` 強制刷新流程未改動。預設頁面仍開啟核心行情分頁；切換第五個分頁後，才呈現復盤摘要、行情基準、五項評分規則、四級分級與 10 檔逐檔評分卡。

本輪前端/資料快取版本為 `20260829-weekly-tab-r1`。這只是分頁結構版本，不代表新增行情日期；週評基準仍為 `2026-08-28`。部署後需重新檢查 GitHub Pages 的第五個分頁與 Render 公網刷新回傳是否仍包含 `weekly_review`、Shioaji 10/10、TWSE 10/10。

本机桥接服务仅用于开发或公网网关故障排查：

```bash
python3 dashboard_server.py
```

然后打开 `http://127.0.0.1:8765/`。按钮会调用本机 `POST /api/refresh`；这不是公网使用路径。

### 3. 单独重新生成 iCloud 桌面 Excel
```bash
python3 /Users/TonyFu/Desktop/台湾股市分析/create_shioaji_excel.py
```

### 4. 多端调阅公网 Dashboard
在 iPhone、iPad、Mac 或任意浏览器打开：
`https://tonytcfu.github.io/taiwan-stock-analysis/`

---

## 六、 风控提示与后续扩展建议

1. **财务预告日跟踪**: 鸿海即将在 2026-08-14（本周五）举办法说会，建议关注其 GB200 出货量及毛利率指导。
2. **凭证保护**: `.shioaji.local.env` 严禁提交至 Git 仓库；公网网关凭证只配置在 Render 环境变量，不复制到 GitHub Pages、前端代码、日志或 JSON。
3. **扩展标的池**: 如需新增台股标的（如散热双雄双鸿 3324 或 CCL 龙头台燿 6274），只需修改 `fetch_shioaji_data.py` 中的 `STOCK_LIST` 字典即可。
