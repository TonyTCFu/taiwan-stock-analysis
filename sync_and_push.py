#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾股市分析 - 自动化 Shioaji 数据同步、Excel 更新与公网 GitHub Pages 部署脚本
"""
import os
import sys
import subprocess
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_cmd(cmd, cwd=ROOT):
    print(f"--> 执行: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"警告/错误: {res.stderr}")
    else:
        print(f"成功: {res.stdout.strip()}")
    return res.returncode == 0

def main():
    print("=== 1. 刷新 Shioaji 主源 / TWSE MIS 降级行情（以 STOCKS_META 全部标的为准） ===")
    if not run_cmd(f"{sys.executable} fetch_shioaji_data.py"):
        raise SystemExit("行情刷新失败，已停止后续 Excel、commit 和 push，避免发布陈旧数据。")

    print("\n=== 2. 重新绘制并更新 iCloud 桌面 Excel 研报 ===")
    if not run_cmd(f"{sys.executable} create_shioaji_excel.py"):
        raise SystemExit("Excel 更新失败，已停止 commit 和 push。")

    print("\n=== 3. 提交代码并自动化推送到公网 (GitHub Pages) ===")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ver_tag = datetime.datetime.now().strftime("v%Y%m%d_%H%M%S")
    
    run_cmd("git add .")
    run_cmd(f'git commit -m "update: Shioaji 实时行情同步 [{now_str}] ({ver_tag})"')
    run_cmd("gh auth setup-git")
    run_cmd("git push origin main")

    print(f"\n==========================================================================")
    print(f"🎉 公网同步推送完成！版本标签: {ver_tag}")
    print(f"🌐 公网跨端访问链接: https://tonytcfu.github.io/taiwan-stock-analysis/")
    print(f"==========================================================================")

if __name__ == "__main__":
    main()
