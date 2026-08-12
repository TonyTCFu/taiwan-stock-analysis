# AGENTS.md - 台湾股市分析 Dashboard 项目规范

## 项目概况
- **项目名称**: 台湾股市分析 Dashboard (Taiwan Stock Analysis Dashboard)
- **创建日期**: 2026-08-12
- **应用场景**: 针对台股 5 大 AI 核心卡位龙头 (2330, 2059, 2383, 3017, 2317) 的全自动化、响应式、公网可访问的每日行情与 Serenity 风控决策仪表盘。

## 技术栈与设计标准
- **前端**: HTML5 + Vanilla JS + CSS Variables (Modern Dark Mode / Glassmorphism 极简奢华 UI)。
- **字体**: 中文优先 `Microsoft YaHei` / `Noto Sans TC`，英文与数字使用 `Calibri` / `Inter` / `JetBrains Mono`。
- **数据抓取与计算**: Python 3 (`yfinance` / Yahoo Finance API + 自动化买卖区间与指标推算)。
- **自动化部署与公网同步**: GitHub Actions (`.github/workflows/daily_update.yml`) / Vercel / GitHub Pages (自动更新推送至公网链接 `台湾股市分析`)。

## 编码与测试标准
- 页面必须支持 iOS/Android 移动端与桌面端自适应。
- 数据输入必须进行为空防错处理，支持离线 JSON 降级预警。
- 零硬编码密钥，遵守 R.A.I.L.G.U.A.R.D 安全规范。
