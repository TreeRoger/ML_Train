"""Job and training configuration schemas."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelConfig(BaseModel):
    """Model architecture configuration."""
    architecture: str = "resnet18"
    num_classes: int = 10
    pretrained: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)


class TrainingConfig(BaseModel):
    """Training hyperparameters and distributed config."""
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    world_size: int = Field(default=1, ge=1, le=8, description="Simulated GPU workers")
    dataset: str = "cifar10"
    extra: dict[str, Any] = Field(default_factory=dict)


class JobSubmitRequest(BaseModel):
    """Request body for submitting a training job."""
    model_config: ModelConfig = Field(default_factory=ModelConfig)
    training_config: TrainingConfig = Field(default_factory=TrainingConfig)
    name: Optional[str] = None


class JobSubmitResponse(BaseModel):
    """Response after job submission."""
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    message: str = "Job queued successfully"
