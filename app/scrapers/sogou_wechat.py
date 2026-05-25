"""搜狗微信搜索 — 抓取微信公众号文章。"""

import time
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import PlatformScraper, ScrapeResult
from app.scrapers.user_agents import random_ua
from app.core.retry import with_retry


class SogouWechatScraper(PlatformScraper):
    platform_id = "sogou_wechat"
    platform_name = "微信"
    platform_icon = "💬"

    async def search(self, query: str, max_results: int = 10) -> ScrapeResult:
        start = time.monotonic()
        try:
            results = await with_retry(
                lambda: self._do_search(query, max_results),
                max_retries=2,
                base_delay=1.5,
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

    async def _do_search(self, query: str, max_results: int) -> list[dict]:
        url = f"https://weixin.sogou.com/weixin?type=2&query={quote(query)}"
        headers = {
            "User-Agent": random_ua(),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://weixin.sogou.com/",
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        text = resp.text
        if "请输入验证码" in text or "antispider" in text.lower():
            raise RuntimeError("搜狗微信触发验证码，请稍后重试")

        soup = BeautifulSoup(text, "lxml")
        results = []

        for item in soup.select(".news-list li")[:max_results]:
            title_el = item.select_one("h3 a")
            if not title_el:
                continue

            snippet_el = item.select_one(".txt-info")
            source_el = item.select_one(".s-p") or item.select_one(".account")

            href = title_el.get("href", "")
            if href.startswith("/"):
                href = f"https://weixin.sogou.com{href}"

            result = {
                "title": title_el.get_text(strip=True),
                "url": href,
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            }
            if source_el:
                result["snippet"] = (
                    f"[{source_el.get_text(strip=True)}] {result['snippet']}"
                )

            results.append(result)

        return results