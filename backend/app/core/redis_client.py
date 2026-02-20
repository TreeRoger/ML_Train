"""Redis client for job queue and metrics pub/sub."""

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings


class RedisClient:
    """Async Redis client for queue and pub/sub."""

    QUEUE_KEY = "ml_train:job_queue"
    JOB_PREFIX = "ml_train:job:"
    METRICS_CHANNEL = "ml_train:metrics"
    JOB_STATUS_PREFIX = "ml_train:job_status:"

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected")
        return self._client

    async def enqueue_job(self, job_id: str, payload: dict[str, Any]) -> None:
        """Add job to the queue."""
        await self.client.lpush(self.QUEUE_KEY, json.dumps({"job_id": job_id, **payload}))

    async def get_job_data(self, job_id: str) -> dict | None:
        """Get stored job data."""
        data = await self.client.get(f"{self.JOB_PREFIX}{job_id}")
        return json.loads(data) if data else None

    async def set_job_data(self, job_id: str, data: dict[str, Any], ttl: int = 86400) -> None:
        """Store job data with TTL (default 24h)."""
        await self.client.setex(
            f"{self.JOB_PREFIX}{job_id}",
            ttl,
            json.dumps(data),
        )

    async def set_job_status(self, job_id: str, status: str, extra: dict | None = None) -> None:
        """Update job status in Redis."""
        key = f"{self.JOB_STATUS_PREFIX}{job_id}"
        data = {"status": status, **(extra or {})}
        await self.client.setex(key, 86400, json.dumps(data))

    async def get_job_status(self, job_id: str) -> dict | None:
        """Get job status from Redis."""
        data = await self.client.get(f"{self.JOB_STATUS_PREFIX}{job_id}")
        return json.loads(data) if data else None

    async def publish_metrics(self, job_id: str, metrics: dict[str, Any]) -> None:
        """Publish metrics to channel for collector."""
        await self.client.publish(
            self.METRICS_CHANNEL,
            json.dumps({"job_id": job_id, **metrics}),
        )


redis_client = RedisClient()
