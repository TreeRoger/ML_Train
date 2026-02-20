"""Job submission and queue service."""

import uuid
from typing import Any

from celery import Celery

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.core.redis_client import redis_client
from app.models.job import JobModel
from shared.schemas.job import JobStatus, JobSubmitRequest

settings = get_settings()
celery_app = Celery(
    "orchestrator",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


async def submit_job(request: JobSubmitRequest) -> tuple[str, dict[str, Any]]:
    """
    Submit a training job to the queue.
    Returns (job_id, response_data).
    """
    job_id = str(uuid.uuid4())
    payload = {
        "name": request.name,
        "model_config": request.model_spec.model_dump(),
        "training_config": request.training_config.model_dump(),
    }

    # Store job metadata in Redis
    await redis_client.set_job_data(job_id, {
        "status": JobStatus.QUEUED.value,
        "config": payload,
        "name": request.name,
    })
    await redis_client.set_job_status(job_id, JobStatus.QUEUED.value)

    # Persist to PostgreSQL for list_jobs
    async with async_session_maker() as session:
        job = JobModel(
            id=job_id,
            name=request.name,
            status=JobStatus.QUEUED.value,
            config=payload,
        )
        session.add(job)
        await session.commit()

    # Enqueue to Celery (orchestrator will pick up)
    celery_app.send_task(
        "orchestrator.app.tasks.process_training_job",
        args=[job_id],
        kwargs={"payload": payload},
    )

    return job_id, {
        "job_id": job_id,
        "status": JobStatus.QUEUED.value,
        "message": "Job queued successfully",
    }
