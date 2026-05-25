"""小红书登录助手 — 打开浏览器让用户手动扫码登录，保存 Cookie。

Usage:
  cd search-aggregator && python app/scrapers/xiaohongshu_login.py
  make xhs-login
"""

import asyncio
import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from playwright.async_api import async_playwright

COOKIE_FILE = _PROJECT_ROOT / "data" / "cookies" / "xiaohongshu.json"


async def main():
    print("正在启动浏览器 (非 headless 模式)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        await page.goto("https://www.xiaohongshu.com/explore", wait_until="networkidle", timeout=30000)

        print("\n请在打开的浏览器中扫码登录小红书")
        print("登录成功后回到此处按 Enter 键继续...")
        input()

        cookies = await context.cookies()
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"\nCookie 已保存到 {COOKIE_FILE}")
        print("现在可以正常使用小红书搜索了。")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())