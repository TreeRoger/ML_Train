"""FastAPI application entrypoint."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jobs import router as jobs_router
from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.redis_client import redis_client


_metrics_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect Redis, create tables, start metrics collector. Shutdown: disconnect."""
    global _metrics_task
    await redis_client.connect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.metrics_collector import start_metrics_collector_background
    _metrics_task = start_metrics_collector_background()

    yield

    if _metrics_task:
        _metrics_task.cancel()
        try:
            await _metrics_task
        except asyncio.CancelledError:
            pass
    await redis_client.disconnect()


app = FastAPI(
    title="ML Training Orchestrator",
    description="Kubernetes-based distributed ML training job orchestration",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix=settings.api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
