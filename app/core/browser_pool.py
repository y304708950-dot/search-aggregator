"""Playwright 浏览器池 — 复用 Chromium 实例，避免每次搜索都启动浏览器。"""

import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.scrapers.user_agents import random_ua

from playwright.async_api import async_playwright, Browser, BrowserContext


class BrowserPool:
    def __init__(self, pool_size: int = 2):
        self.pool_size = pool_size
        self._playwright = None
        self._browser: Browser | None = None
        self._available: asyncio.Queue[BrowserContext] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(pool_size)
        self._created = 0

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

    async def stop(self):
        while not self._available.empty():
            try:
                ctx = self._available.get_nowait()
                await ctx.close()
            except Exception:
                pass
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @asynccontextmanager
    async def acquire(self, is_mobile: bool = False):
        await self._semaphore.acquire()
        ctx = None
        try:
            ctx = await self._get_or_create_context(is_mobile)
            yield ctx
        finally:
            if ctx:
                await self._return_context(ctx)
            self._semaphore.release()

    async def _get_or_create_context(self, is_mobile: bool) -> BrowserContext:
        try:
            return self._available.get_nowait()
        except asyncio.QueueEmpty:
            if self._created < self.pool_size:
                self._created += 1
                viewport = (
                    {"width": 390, "height": 844}
                    if is_mobile
                    else {"width": 1280, "height": 800}
                )
                return await self._browser.new_context(
                    viewport=viewport,
                    user_agent=random_ua(),
                )
            return await self._available.get()

    async def _return_context(self, ctx: BrowserContext):
        await ctx.clear_cookies()
        self._available.put_nowait(ctx)


browser_pool = BrowserPool(pool_size=settings.browser_pool_size)