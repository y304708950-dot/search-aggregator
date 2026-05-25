# 搜索聚合器配置

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "搜索聚合器"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # 搜索配置
    max_results_per_platform: int = 10
    search_timeout: int = 30
    overall_timeout: int = 60

    # 缓存配置
    cache_dir: str = "data/cache"
    cache_default_ttl: int = 1800

    # Playwright 配置
    browser_pool_size: int = 2
    browser_headless: bool = True
    disable_browser: bool = False  # 服务器环境可禁用浏览器（节省资源）

    # 代理配置（可选）
    http_proxy: str | None = None
    https_proxy: str | None = None


settings = Settings()