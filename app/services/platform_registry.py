"""平台注册表 — 管理所有可用的搜索器。"""

from app.scrapers.base import PlatformScraper
from app.scrapers.web import WebScraper
from app.scrapers.sogou_wechat import SogouWechatScraper
from app.scrapers.xiaohongshu import XiaohongshuScraper

_registry: list[PlatformScraper] = []


def _build_registry() -> list[PlatformScraper]:
    scrapers: list[PlatformScraper] = [
        WebScraper(),
        SogouWechatScraper(),
        XiaohongshuScraper(),  # Cookie 模式，无需浏览器
    ]
    return scrapers


def get_registry() -> list[PlatformScraper]:
    global _registry
    if not _registry:
        _registry = _build_registry()
    return _registry


def get_enabled_scrapers(platforms: list[str] | None = None) -> list[PlatformScraper]:
    all_scrapers = get_registry()
    if platforms is None or "all" in platforms:
        return [s for s in all_scrapers if s.enabled]
    requested = set(platforms)
    return [s for s in all_scrapers if s.enabled and s.platform_id in requested]


def get_all_platform_ids() -> list[str]:
    return [s.platform_id for s in get_registry()]