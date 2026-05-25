"""搜索 API — SSE 流式端点。"""

import json
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import SearchRequest, SearchJobResponse
from app.services.orchestrator import SearchOrchestrator

router = APIRouter(prefix="/api")
orchestrator = SearchOrchestrator()

# 内存中的任务记录
_active_jobs: dict[str, dict] = {}


@router.post("/search", response_model=SearchJobResponse)
async def create_search(request: SearchRequest) -> dict:
    job_id = str(uuid.uuid4())[:8]
    _active_jobs[job_id] = {
        "query": request.query,
        "platforms": request.platforms,
        "max_results": request.max_results,
        "skip_cache": request.skip_cache,
        "created_at": time.time(),
    }
    return {"job_id": job_id, "stream_url": f"/api/search/{job_id}/stream"}


@router.get("/search/{job_id}/stream")
async def stream_results(job_id: str):
    job = _active_jobs.get(job_id)
    if not job:
        async def error_gen():
            yield f"event: error\ndata: {json.dumps({'error': '任务不存在或已过期'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    async def event_generator():
        platform_count = 0
        async for result in orchestrator.search_all(
            query=job["query"],
            platforms=job["platforms"],
            max_results=job["max_results"],
            skip_cache=job.get("skip_cache", False),
        ):
            platform_count += 1
            payload = json.dumps({
                "platform": result.platform,
                "results": result.results,
                "error": result.error,
                "cached": result.cached,
                "elapsed_ms": result.elapsed_ms,
            }, ensure_ascii=False)
            yield f"event: platform_result\ndata: {payload}\n\n"

        yield f"event: complete\ndata: {json.dumps({'total_platforms': platform_count})}\n\n"
        _active_jobs.pop(job_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )