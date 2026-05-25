"""SearchOrchestrator — 协调所有平台的并发搜索。"""

import asyncio
import time

from app.core.cache import get_cached, set_cache
from app.scrapers.base import PlatformScraper, ScrapeResult
from app.services.platform_registry import get_enabled_scrapers


class SearchOrchestrator:
    async def search_all(
        self,
        query: str,
        platforms: list[str] | None = None,
        max_results: int = 10,
        skip_cache: bool = False,
    ):
        scrapers = get_enabled_scrapers(platforms)
        if not scrapers:
            return

        # 先处理缓存命中的
        remaining: list[PlatformScraper] = []
        for scraper in scrapers:
            if not skip_cache:
                cached = get_cached(query, scraper.platform_id)
                if cached is not None:
                    yield ScrapeResult(
                        platform=scraper.platform_id,
                        query=query,
                        results=cached,
                        cached=True,
                        elapsed_ms=0,
                    )
                    continue
            remaining.append(scraper)

        if not remaining:
            return

        # 并发搜索所有剩余平台
        tasks: dict[asyncio.Task, PlatformScraper] = {}
        for scraper in remaining:
            task = asyncio.create_task(
                self._run_with_timing(scraper, query, max_results)
            )
            tasks[task] = scraper

        # 逐个收集完成的结果
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        while done:
            for completed_task in done:
                scraper = tasks.pop(completed_task)
                try:
                    result = completed_task.result()
                except Exception as e:
                    result = ScrapeResult(
                        platform=scraper.platform_id,
                        query=query,
                        results=[],
                        error=str(e),
                    )

                if result.results and not result.error:
                    set_cache(query, scraper.platform_id, result.results)

                yield result

            if pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            else:
                break

    async def _run_with_timing(
        self,
        scraper: PlatformScraper,
        query: str,
        max_results: int,
    ) -> ScrapeResult:
        start = time.monotonic()
        result = await scraper.search(query, max_results)
        result.elapsed_ms = (time.monotonic() - start) * 1000
        return result