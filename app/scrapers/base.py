"""各平台搜索器的抽象基类。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ScrapeResult:
    platform: str
    query: str
    results: list[dict] = field(default_factory=list)
    error: str | None = None
    cached: bool = False
    elapsed_ms: float = 0.0


class PlatformScraper(ABC):
    """每个平台搜索器必须继承此基类。"""

    platform_id: str
    platform_name: str
    platform_icon: str = ""
    requires_browser: bool = False
    enabled: bool = True

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> ScrapeResult:
        ...

    def to_dict(self) -> dict:
        return {
            "id": self.platform_id,
            "name": self.platform_name,
            "icon": self.platform_icon,
            "requires_browser": self.requires_browser,
            "enabled": self.enabled,
        }