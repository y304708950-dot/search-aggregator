"""Pydantic 数据模型。"""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    platforms: list[str] | None = None  # None 或 ["all"] 表示全部平台
    max_results: int = 10
    skip_cache: bool = False


class PlatformInfo(BaseModel):
    id: str
    name: str
    icon: str
    requires_browser: bool
    enabled: bool


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str = ""


class PlatformResult(BaseModel):
    platform: str
    platform_name: str
    platform_icon: str
    results: list[SearchResultItem]
    error: str | None = None
    cached: bool = False
    elapsed_ms: float = 0.0


class SearchJobResponse(BaseModel):
    job_id: str
    stream_url: str