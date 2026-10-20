from __future__ import annotations

import logging
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.db import init_db
from app.routes.applications import router as applications_router
from app.routes.jobs import router as jobs_router
from app.routes.overview import router as overview_router
from app.routes.preferences import router as preferences_router
from app.routes.recommendations import router as recommendations_router
from app.routes.resumes import router as resumes_router
from app.routes.settings import router as settings_router
from app.services.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)
settings = get_settings()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """记录每个请求的耗时。"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > 500:
            logger.warning("Slow request: %s %s took %.0fms", request.method, request.url.path, elapsed_ms)
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
        return response


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="make-jobs-ai backend", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)
# CORSMiddleware 必须最后添加（最外层），否则预检请求无法正确返回 CORS 头
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 全局异常处理（注意：不要在这里返回 JSONResponse，会绕过 CORS 中间件）
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    dashboard_path = Path(__file__).parent / "static" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


app.include_router(overview_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(recommendations_router)
app.include_router(preferences_router)
app.include_router(settings_router)
