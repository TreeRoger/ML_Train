"""Background service: subscribe to Redis metrics channel, store in PostgreSQL."""

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as redis
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.models.job import JobModel, MetricModel

logger = logging.getLogger(__name__)
METRICS_CHANNEL = "ml_train:metrics"


async def store_metric(job_id: str, step: int, epoch: float, name: str, value: float):
    """Insert or update metric in DB."""
    async with async_session_maker() as session:
        metric = MetricModel(
            job_id=job_id,
            step=step,
            epoch=epoch,
            name=name,
            value=value,
        )
        session.add(metric)
        await session.commit()


async def ensure_job_exists(job_id: str) -> None:
    """Create job record if missing (for metrics from Redis-only jobs)."""
    async with async_session_maker() as session:
        r = await session.execute(select(JobModel).where(JobModel.id == job_id))
        if r.scalar_one_or_none() is None:
            job = JobModel(id=job_id, status="running", config={})
            session.add(job)
            await session.commit()


async def run_metrics_collector():
    """Subscribe to Redis metrics channel and persist to PostgreSQL."""
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(METRICS_CHANNEL)
    logger.info(f"Subscribed to {METRICS_CHANNEL}")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                job_id = data.get("job_id")
                step = data.get("step", 0)
                epoch = data.get("epoch", 0.0)
                if not job_id:
                    continue
                await ensure_job_exists(job_id)
                for key in ("loss", "accuracy"):
                    if key in data:
                        await store_metric(job_id, step, epoch, key, float(data[key]))
            except Exception as e:
                logger.exception("Metrics collect error: %s", e)
    finally:
        await pubsub.unsubscribe(METRICS_CHANNEL)
        await client.close()


def start_metrics_collector_background():
    """Start collector in a background task."""
    async def _run():
        while True:
            try:
                await run_metrics_collector()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Metrics collector crashed: %s", e)
                await asyncio.sleep(5)

    return asyncio.create_task(_run())
