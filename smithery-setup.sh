#!/usr/bin/env bash
# smithery-setup.sh — Finance MCP Server 출판 스크립트
# 실행 전 준비사항:
#   1. GitHub: kimnam1/finance-mcp repo 생성 (public)
#   2. Node.js 설치: sudo apt install nodejs npm (또는 nvm)
#   3. smithery CLI: npm install -g @smithery/cli
#   4. smithery login (GitHub OAuth)

set -e

GITHUB_USER="kimnam1"
REPO="finance-mcp"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO}"

echo "=== Finance MCP Server — Smithery 출판 ==="
echo ""

# 1. GitHub 리포 초기화 (로컬)
echo "[1/4] Git 리포 초기화..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".git" ]; then
  git init
  git remote add origin "git@github.com:${GITHUB_USER}/${REPO}.git"
fi

git add server.py README.md requirements.txt smithery-setup.sh
git commit -m "feat: Finance MCP v0.4.0 — 15 tools, no API key"
git branch -M main
git push -u origin main

echo "  ✓ GitHub push 완료: ${REPO_URL}"
echo ""

# 2. smithery 등록
echo "[2/4] Smithery CLI 버전 확인..."
smithery --version || { echo "ERROR: smithery CLI not found. Run: npm install -g @smithery/cli"; exit 1; }

echo ""
echo "[3/4] Smithery에 MCP 서버 게시..."
smithery mcp publish "${REPO_URL}" -n "${GITHUB_USER}/${REPO}"

echo ""
echo "[4/4] 추가 디렉토리 등록 링크:"
echo "  - mcp.so:   https://mcp.so/submit"
echo "  - LobeHub:  https://lobehub.com/mcp (PR 방식)"
echo "  - MCPize:   https://mcpize.com (수익화 플랫폼)"
echo ""
echo "=== 완료! ==="
