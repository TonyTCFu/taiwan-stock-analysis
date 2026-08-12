# AGENTS.md - 台湾股市分析项目规范

## 项目基本信息
* **项目名称**: 台湾股市分析 (Taiwan Stock Analysis)
* **创建日期**: 2026-08-12
* **项目工作区**: `/Users/TonyFu/Desktop/台湾股市分析`
* **技术栈**: Python 3 (Shioaji SDK / Quant models / Openpyxl / Pandas) + Web Front-end (HTML5 / Vanilla JS / Glassmorphism CSS) + CI/CD (GitHub Pages / GitHub Actions)

## 核心功能与技能集成 (Skill Integrations)
1. **Shioaji 台湾股市实时行情与筹码 (`shioaji-taiwan-stock`)**
   - 永丰金 Shioaji API 直连 TWSE 交易所盘口，获取实时 K 线、Tick 数据、收盘价及三大法人（外资、投信、自营商）筹码进出。
2. **瓶颈猎手与供应链拆解 (`serenity-hunter` & `robotics-bottleneck-analyst`)**
   - 逆向供应链拆解（下游大厂 -> 中游器件 -> 最上游核心材料），挖掘处于绝对卡脖子瓶颈（如 CoWoS 封装、精密滑轨、高阶 CCL、液冷散热）的冷门龙头企业。
3. **九步估值与风控审核 (`serenity-analyst`)**
   - 针对候选个股执行 9 步审核（卡点打分、3 级证据阶梯、8 个罚分因子扫描）。评分 $\ge 80$ 分建议重仓，60-79 分试仓，$<60$ 分排除。
4. **台股量化选股 (`finlab`)**
   - 自动化选股模型，结合财务报表、进出口数据与筹码沉淀进行量化验证。

## 编码与工程标准
* **架构设计原则**: 遵从 Karpathy Guidelines + Ponytail 控复杂度原则。优先朴素易维护方案，避免过度抽象。
* **UI & Dashboard 规范**: 
  - 极简奢华暗黑 Glassmorphism 界面，适配 Desktop / Tablet / Mobile 响应式布局。
  - 中文字体统一使用 `Microsoft YaHei` / `PingFang SC`，英文字体与数字统一使用 `Calibri` / `Inter` / `JetBrains Mono`。
  - 强制防缓存机制 (`Cache-Control: no-cache`) 与优雅数据降级保护。
* **安全规范 R.A.I.L.G.U.A.R.D**:
  - **Risk-First**: 禁止在代码、配置、日志或 Markdown 文件中硬编码 API Key、密匙或 Token。
  - **Local Defaults**: 本地凭证统一读取安全环境文件（例如 `/Users/TonyFu/Documents/台股量化Antigravity/.shioaji.local.env`）。
* **测试与部署流程**:
  - 所有自动化脚本（如 `fetch_shioaji_data.py`, `create_shioaji_excel.py`, `sync_and_push.py`）需本地真实样本校验无误后方能提交 commit 并 Push 到 GitHub Pages。
