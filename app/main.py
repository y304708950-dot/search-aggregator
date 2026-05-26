"""搜索聚合器 — FastAPI 应用入口。"""

from contextlib import asynccontextmanager

import json

import jinja2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.config import settings
from app.core.browser_pool import browser_pool
from app.core.cache import cache
from app.routers import search, platforms
from app.services.platform_registry import get_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.disable_browser:
        await browser_pool.start()
    yield
    if not settings.disable_browser:
        await browser_pool.stop()
    cache.close()


app = FastAPI(title="搜索聚合器", lifespan=lifespan)
app.include_router(search.router)
app.include_router(platforms.router)

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("app/templates"),
    autoescape=True,
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ps = get_registry()
    platforms_list = [s.to_dict() for s in ps]
    template = _jinja_env.get_template("index.html")
    html = template.render(
        request=request,
        platforms=platforms_list,
        platforms_json=json.dumps(platforms_list, ensure_ascii=False),
    )
    return HTMLResponse(html)
