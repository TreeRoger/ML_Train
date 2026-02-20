"""Job submission and query API."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import redis_client
from app.models.job import JobModel, MetricModel
from app.services.job_service import submit_job
from shared.schemas.job import JobSubmitRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("")
async def create_job(
    request: JobSubmitRequest,
) -> dict[str, Any]:
    """Submit a new training job. Returns job_id and status."""
    job_id, data = await submit_job(request)
    return data


@router.get("")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    status: str | None = None,
) -> dict[str, Any]:
    """List jobs with optional status filter."""
    q = select(JobModel).order_by(JobModel.created_at.desc()).limit(limit)
    if status:
        q = q.where(JobModel.status == status)
    result = await db.execute(q)
    jobs = result.scalars().all()
    return {
        "jobs": [
            {
                "id": j.id,
                "name": j.name,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get job details. Merges Redis status with DB if available."""
    # Try Redis first (real-time status)
    redis_status = await redis_client.get_job_status(job_id)
    if redis_status:
        job_data = await redis_client.get_job_data(job_id)
        status = redis_status.get("status", "unknown")
        # Sync status to DB for list consistency
        result = await db.execute(select(JobModel).where(JobModel.id == job_id))
        job_row = result.scalar_one_or_none()
        if job_row and job_row.status != status:
            job_row.status = status
            job_row.k8s_job_name = redis_status.get("k8s_job_name")
            await db.commit()
        return {
            "id": job_id,
            "name": job_data.get("name") if job_data else None,
            "status": status,
            "config": job_data.get("config", {}) if job_data else {},
            "k8s_job_name": redis_status.get("k8s_job_name"),
            "source": "redis",
        }

    # Fallback to DB
    result = await db.execute(select(JobModel).where(JobModel.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "name": job.name,
        "status": job.status,
        "config": job.config,
        "k8s_job_name": job.k8s_job_name,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "source": "db",
    }


@router.get("/{job_id}/metrics")
async def get_job_metrics(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    metric_name: str | None = None,
) -> dict[str, Any]:
    """Get training metrics for a job."""
    q = select(MetricModel).where(MetricModel.job_id == job_id).order_by(MetricModel.step)
    if metric_name:
        q = q.where(MetricModel.name == metric_name)
    result = await db.execute(q)
    metrics = result.scalars().all()
    # Group by name for frontend
    by_name: dict[str, list[dict]] = {}
    for m in metrics:
        by_name.setdefault(m.name, []).append({
            "step": m.step,
            "epoch": m.epoch,
            "value": m.value,
        })
    return {"job_id": job_id, "metrics": by_name}
