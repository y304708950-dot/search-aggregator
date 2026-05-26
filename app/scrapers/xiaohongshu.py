"""小红书搜索 — 通过 API + Cookie 认证抓取。"""

import json
import os
import time
from pathlib import Path

import httpx

from app.scrapers.base import PlatformScraper, ScrapeResult
from app.scrapers.user_agents import random_ua
from app.core.retry import with_retry

COOKIE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "cookies" / "xiaohongshu.json"


def _load_cookies() -> dict[str, str] | None:
    """优先从环境变量 XHS_COOKIES 读取，其次从文件读取。"""
    # 1. 环境变量（Render 等部署环境）
    env_cookies = os.environ.get("XHS_COOKIES")
    if env_cookies:
        try:
            cookies_list = json.loads(env_cookies)
            if isinstance(cookies_list, list):
                return {c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c}
            elif isinstance(cookies_list, dict):
                return cookies_list
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. 本地文件
    if COOKIE_FILE.exists():
        try:
            with open(COOKIE_FILE) as f:
                cookies_list = json.load(f)
            if isinstance(cookies_list, list):
                return {c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c}
            elif isinstance(cookies_list, dict):
                return cookies_list
        except Exception:
            return None

    return None


class XiaohongshuScraper(PlatformScraper):
    platform_id = "xiaohongshu"
    platform_name = "小红书"
    platform_icon = "📕"
    requires_browser = True
    enabled = True

    async def search(self, query: str, max_results: int = 10) -> ScrapeResult:
        start = time.monotonic()
        cookies = _load_cookies()

        if not cookies:
            elapsed = (time.monotonic() - start) * 1000
            return ScrapeResult(
                platform=self.platform_id,
                query=query,
                results=[],
                error="需要登录：请在 Render 环境变量中设置 XHS_COOKIES（浏览器 Cookie JSON）",
                elapsed_ms=elapsed,
            )

        try:
            results = await with_retry(
                lambda: self._search_api(query, max_results, cookies),
                max_retries=2,
                base_delay=1.0,
            )
            elapsed = (time.monotonic() - start) * 1000
            return ScrapeResult(
                platform=self.platform_id,
                query=query,
                results=results,
                elapsed_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return ScrapeResult(
                platform=self.platform_id,
                query=query,
                results=[],
                error=str(e),
                elapsed_ms=elapsed,
            )

    async def _search_api(
        self, query: str, max_results: int, cookies: dict[str, str]
    ) -> list[dict]:
        headers = {
            "User-Agent": random_ua(),
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
        }

        payload = {
            "keyword": query,
            "page": 1,
            "page_size": max_results,
            "search_id": str(int(time.time() * 1000)),
            "sort": "general",
            "note_type": 0,
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.post(
                "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
                headers=headers,
                json=payload,
                cookies=cookies,
            )
            resp.raise_for_status()

        data = resp.json()
        if not data.get("success"):
            msg = data.get("msg", "未知错误")
            raise RuntimeError(f"小红书 API 返回错误: {msg}")

        results = []
        for item in data.get("data", {}).get("items", [])[:max_results]:
            note = item.get("note_card") or item
            note_id = item.get("id", "")
            title = note.get("display_title", "")
            desc = note.get("desc", "")
            results.append({
                "title": title or desc[:40] or "(无标题)",
                "url": f"https://www.xiaohongshu.com/explore/{note_id}",
                "snippet": desc[:120] if desc else "",
            })

        return results
