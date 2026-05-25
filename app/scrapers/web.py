"""综合网页搜索 — 百度优先，DuckDuckGo 备选。"""

import re
import time
from urllib.parse import quote, unquote

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import PlatformScraper, ScrapeResult
from app.scrapers.user_agents import random_ua
from app.core.retry import with_retry


def _extract_ddg_url(link: str) -> str:
    m = re.search(r"uddg=(https?%3A[^&]+)", link)
    if m:
        return unquote(m.group(1))
    return link


class WebScraper(PlatformScraper):
    platform_id = "web"
    platform_name = "综合网页"
    platform_icon = "🌐"

    async def search(self, query: str, max_results: int = 10) -> ScrapeResult:
        start = time.monotonic()
        results, error = [], None

        try:
            results = await self._search_baidu(query, max_results)
        except Exception as e:
            error = str(e)

        if not results:
            try:
                results = await self._search_ddg(query, max_results)
                error = None
            except Exception as e2:
                if not error:
                    error = str(e2)

        elapsed = (time.monotonic() - start) * 1000
        return ScrapeResult(
            platform=self.platform_id,
            query=query,
            results=results,
            error=error if not results else None,
            elapsed_ms=elapsed,
        )

    async def _search_baidu(self, query: str, max_results: int) -> list[dict]:
        url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results}"
        headers = {
            "User-Agent": random_ua(),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        for container in soup.select(".c-container")[:max_results]:
            title_el = container.select_one("h3 a")
            if not title_el:
                continue
            snippet_el = container.select_one(".c-abstract") or container.select_one(".content-right_8Zs40")
            href = title_el.get("href", "")
            if href.startswith("/"):
                href = f"https://www.baidu.com{href}"
            results.append({
                "title": title_el.get_text(strip=True),
                "url": href,
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })

        return results

    async def _search_ddg(self, query: str, max_results: int) -> list[dict]:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        headers = {
            "User-Agent": random_ua(),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        for item in soup.select(".result")[:max_results]:
            title_el = item.select_one(".result__title a") or item.select_one("a.result__a")
            if not title_el:
                continue
            snippet_el = item.select_one(".result__snippet")
            results.append({
                "title": title_el.get_text(strip=True),
                "url": _extract_ddg_url(title_el.get("href", "")),
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })

        return results