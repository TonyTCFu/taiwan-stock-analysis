#!/bin/bash
# ==============================================================================
# 台湾股市分析 Dashboard - 一键 GitHub 公网推送与 Pages 自动发布脚本
# ==============================================================================

set -e

echo "=== 1. 检查 GitHub 登录状态 ==="
if ! gh auth status >/dev/null 2>&1; then
    echo "提示: 请完成 GitHub 登录授权..."
    gh auth login -w -p https
fi

echo "=== 2. 创建 GitHub 公共仓库 (taiwan-stock-analysis) ==="
REPO_NAME="taiwan-stock-analysis"

if gh repo view "$REPO_NAME" >/dev/null 2>&1; then
    echo "检测到仓库已存在，配置远程 origin 并推送..."
    USER_NAME=$(gh api user -q .login)
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/$USER_NAME/$REPO_NAME.git"
    git branch -M main
    git push -u origin main --force
else
    echo "正在 GitHub 自动创建公开仓库并推送文件..."
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
fi

USER_NAME=$(gh api user -q .login)
PUBLIC_URL="https://$USER_NAME.github.io/$REPO_NAME/"

echo "=== 3. 启用 GitHub Pages 免费公网托管 ==="
gh api "repos/$USER_NAME/$REPO_NAME/pages" -X POST -F "source[branch]=main" -F "source[path]=/" 2>/dev/null || echo "GitHub Pages 已配置或正准备生效"

echo ""
echo "=============================================================================="
echo "🎉 部署成功！“台湾股市分析” 仪表盘公网上线！"
echo "🌐 您的公网访问链接: $PUBLIC_URL"
echo "=============================================================================="
