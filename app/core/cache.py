"""diskcache 缓存层 — SQLite 后端，无需外部进程。"""

import hashlib
from app.config import settings

import diskcache

cache = diskcache.Cache(settings.cache_dir)

CACHE_TTL = {
    "web": 3600,
    "bilibili": 1800,
    "zhihu": 1800,
    "douban": 3600,
    "sogou_wechat": 1800,
    "xiaohongshu": 600,
    "douyin": 600,
    "jike": 1800,
}


def _cache_key(query: str, platform: str) -> str:
    raw = f"{platform}:{query.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(query: str, platform: str) -> list[dict] | None:
    key = _cache_key(query, platform)
    return cache.get(key)


def set_cache(query: str, platform: str, results: list[dict]) -> None:
    key = _cache_key(query, platform)
    ttl = CACHE_TTL.get(platform, settings.cache_default_ttl)
    cache.set(key, results, expire=ttl)