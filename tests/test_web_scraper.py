"""Web scraper tests."""

import pytest

from app.scrapers.web import WebScraper, _extract_ddg_url


@pytest.mark.asyncio
async def test_web_scraper_returns_results():
    scraper = WebScraper()
    result = await scraper.search("test", max_results=3)
    assert result.platform == "web"
    assert result.error is None or len(result.results) > 0
    for r in result.results:
        assert "title" in r
        assert "url" in r


class TestExtractDdgUrl:
    def test_extract_valid_url(self):
        link = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&rut=abc123"
        assert _extract_ddg_url(link) == "https://example.com"

    def test_extract_non_ddg_url(self):
        assert _extract_ddg_url("https://example.com") == "https://example.com"