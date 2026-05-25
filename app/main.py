"""搜索聚合器 — FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ps = get_registry()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "platforms": [s.to_dict() for s in ps]},
    )