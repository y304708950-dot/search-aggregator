"""指数退避重试。"""

import asyncio
import random
from collections.abc import Callable, Awaitable

import httpx


async def with_retry(
    coro_factory: Callable[[], Awaitable],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> object:
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except (httpx.HTTPStatusError, httpx.ReadTimeout) as e:
            if attempt == max_retries - 1:
                raise
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)
            elif isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500:
                await asyncio.sleep(2**attempt)
            else:
                raise
        except httpx.ConnectError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (2**attempt))