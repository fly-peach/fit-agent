---
name: browser-use-skills
description: 浏览器自动化技能。通过 Playwright 执行打开页面、点击、输入、截图和文本提取等任务。
version: 1.0.0
enabled: true
tags: [browser, automation, playwright]
---

# Browser Use Skills

你是网页自动化助手。此技能用于在需要真实页面交互时执行浏览器操作。

## 技能边界（强制）

- 本技能仅通过 `python scripts/browser_use_cli.py ...` 调用。
- 需要命令执行能力：`execute_shell_command`。
- 默认使用无头浏览器（headless）；仅在用户明确要求可视化时使用 `--headed`。

## 可用命令

```bash
# 打开页面并可选截图/提取文本
python scripts/browser_use_cli.py visit \
  --url "https://example.com" \
  --wait-ms 1200 \
  --screenshot "artifacts/example.png" \
  --extract-selector "h1"

# 点击元素
python scripts/browser_use_cli.py click \
  --url "https://example.com/login" \
  --selector "button[type='submit']" \
  --wait-ms 800

# 输入文本
python scripts/browser_use_cli.py type \
  --url "https://example.com/login" \
  --selector "input[name='email']" \
  --text "demo@example.com" \
  --wait-ms 500
```

## 参数说明

- `--url`：目标页面 URL（必填）。
- `--selector`：CSS 选择器（`click/type` 必填）。
- `--text`：输入文本（`type` 必填）。
- `--wait-ms`：动作后等待毫秒数，默认 `800`。
- `--screenshot`：保存截图路径（可选，支持相对路径）。
- `--extract-selector`：提取指定元素文本（可选）。
- `--headed`：使用可视化浏览器窗口（可选）。

## 返回结果

CLI 输出 JSON，包含：

- `success`：是否成功
- `action`：执行动作
- `url`：访问 URL
- `screenshot`：截图文件路径（如果有）
- `extracted_text`：提取文本（如果有）
- `error`：失败原因（失败时）

## 前置依赖

```bash
pip install playwright
python -m playwright install
```

