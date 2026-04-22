#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBPAGE_DIR="$ROOT_DIR/webpage"
TARGET_DIR="$ROOT_DIR/Rogers/webpage"
LOCK_FILE="$WEBPAGE_DIR/package-lock.json"
NODE_MODULES_DIR="$WEBPAGE_DIR/node_modules"

if [ ! -d "$WEBPAGE_DIR" ]; then
  echo "webpage 目录不存在: $WEBPAGE_DIR" >&2
  exit 1
fi

# 1) 构建前端控制台
cd "$WEBPAGE_DIR"

# Install deps (smart mode)
# FORCE_CI=1      -> always npm ci
# FORCE_INSTALL=1 -> always npm install
# SKIP_INSTALL=1  -> skip installation
INSTALL_FAILED=0
if [ "${SKIP_INSTALL:-0}" = "1" ]; then
  echo "Skip dependency install because SKIP_INSTALL=1"
elif [ "${FORCE_CI:-0}" = "1" ] && [ -f "$LOCK_FILE" ]; then
  if ! npm ci; then INSTALL_FAILED=1; fi
elif [ "${FORCE_INSTALL:-0}" = "1" ]; then
  if ! npm install; then INSTALL_FAILED=1; fi
else
  if [ ! -d "$NODE_MODULES_DIR" ]; then
    if ! npm install; then INSTALL_FAILED=1; fi
  else
    echo "Skip npm install (node_modules is up to date)"
  fi
fi

if [ "${SKIP_INSTALL:-0}" != "1" ] && [ "$INSTALL_FAILED" -eq 1 ]; then
  echo "Install failed, try to clean npm lock dirs and retry..."
  rm -rf "$NODE_MODULES_DIR/.caniuse-lite"* "$NODE_MODULES_DIR/caniuse-lite" || true
  npm cache verify >/dev/null 2>&1 || true
  if [ "${FORCE_CI:-0}" = "1" ] && [ -f "$LOCK_FILE" ]; then
    npm ci
  elif [ "${FORCE_INSTALL:-0}" = "1" ]; then
    npm install
  elif [ -f "$LOCK_FILE" ]; then
    npm ci
  else
    npm install
  fi
fi
if ! npm run build; then
  if [ "${SKIP_INSTALL:-0}" != "1" ] && [ "${FORCE_CI:-0}" != "1" ]; then
    echo "Build failed, retry after npm install..."
    if ! npm install; then
      echo "npm install retry failed, clean node_modules and reinstall..."
      rm -rf "$NODE_MODULES_DIR"
      if [ -f "$LOCK_FILE" ]; then
        npm ci
      else
        npm install
      fi
    fi
    npm run build
  else
    exit 1
  fi
fi

# 2) 复制构建产物到包目录
mkdir -p "$TARGET_DIR"
cp -R "$WEBPAGE_DIR/dist/." "$TARGET_DIR"

echo "Frontend build copied to Rogers/webpage"
