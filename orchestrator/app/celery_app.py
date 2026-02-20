"""Celery application for job orchestration."""

from celery import Celery
from pydantic_settings import BaseSettings


class OrchestratorSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    trainer_image: str = "ml-trainer:latest"
    namespace: str = "ml-train"
    use_k8s: bool = True  # Set False for local dev without K8s

    class Config:
        env_file = ".env"


settings = OrchestratorSettings()

app = Celery(
    "orchestrator",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["orchestrator.app.tasks"],
)
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
