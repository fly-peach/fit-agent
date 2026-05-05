"""Minimal browser-use CLI backed by Playwright."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _ok(**payload):
    return {"success": True, **payload}


def _err(action: str, url: str, exc: Exception):
    return {
        "success": False,
        "action": action,
        "url": url,
        "error": str(exc),
    }


def _ensure_parent(path_str: str) -> str:
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def _run_visit(args: argparse.Namespace):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        if args.wait_ms > 0:
            page.wait_for_timeout(args.wait_ms)

        result = {"action": "visit", "url": args.url}
        if args.extract_selector:
            text = page.locator(args.extract_selector).first.inner_text(timeout=5000)
            result["extracted_text"] = text
        if args.screenshot:
            output = _ensure_parent(args.screenshot)
            page.screenshot(path=output, full_page=True)
            result["screenshot"] = output
        browser.close()
        return _ok(**result)


def _run_click(args: argparse.Namespace):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        page.locator(args.selector).first.click(timeout=8000)
        if args.wait_ms > 0:
            page.wait_for_timeout(args.wait_ms)
        result = {"action": "click", "url": args.url, "selector": args.selector}
        if args.screenshot:
            output = _ensure_parent(args.screenshot)
            page.screenshot(path=output, full_page=True)
            result["screenshot"] = output
        browser.close()
        return _ok(**result)


def _run_type(args: argparse.Namespace):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        locator = page.locator(args.selector).first
        locator.click(timeout=8000)
        locator.fill(args.text, timeout=8000)
        if args.wait_ms > 0:
            page.wait_for_timeout(args.wait_ms)
        result = {
            "action": "type",
            "url": args.url,
            "selector": args.selector,
            "text_length": len(args.text or ""),
        }
        if args.screenshot:
            output = _ensure_parent(args.screenshot)
            page.screenshot(path=output, full_page=True)
            result["screenshot"] = output
        browser.close()
        return _ok(**result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browser use CLI")
    parser.add_argument(
        "action",
        choices=["visit", "click", "type"],
        help="浏览器动作",
    )
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--selector", default="", help="CSS 选择器（click/type 必填）")
    parser.add_argument("--text", default="", help="输入文本（type 必填）")
    parser.add_argument("--wait-ms", type=int, default=800, help="动作后等待毫秒数")
    parser.add_argument("--extract-selector", default="", help="提取文本的 CSS 选择器")
    parser.add_argument("--screenshot", default="", help="截图输出路径")
    parser.add_argument("--headed", action="store_true", help="启用可视化浏览器")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.action in {"click", "type"} and not args.selector:
            raise ValueError("click/type 必须提供 --selector")
        if args.action == "type" and not args.text:
            raise ValueError("type 必须提供 --text")

        if args.action == "visit":
            payload = _run_visit(args)
        elif args.action == "click":
            payload = _run_click(args)
        else:
            payload = _run_type(args)
    except Exception as exc:
        payload = _err(args.action, args.url, exc)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

