# MEMORY.md - 台湾股市分析 Dashboard 架构决策与运维记录

## 架构决策记录 (ADR)
- **2026-08-12**: 选用无后端依赖的纯前端 SPA + GitHub Pages / Vercel 静态托管架构，配合 GitHub Actions / Python 自动化脚本每日收盘后（14:00 TPE）拉取最新行情并更新 `data/stock_data.json`。
- **公网链接标识**: `台湾股市分析` (Taiwan Stock Analysis Dashboard)。

## 数据源与更新机制
- **数据源**: Yahoo Finance API (`2330.TW`, `2059.TW`, `2383.TW`, `3017.TW`, `2317.TW`)。
- **自动抓取脚本**: `fetch_data.py`。
- **部署方式**: 托管于 GitHub Pages / Vercel 或 Cloudflare Pages，公网设备均可跨端读取。
