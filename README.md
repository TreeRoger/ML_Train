# Distributed ML Training Orchestrator

> **Mini Tesla ML Platform** — Kubernetes-based GPU training job orchestration

A production-grade ML training platform featuring async job queues, containerized training on Kubernetes, simulated distributed training, and full observability.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   REST API  │────▶│ Redis Queue  │────▶│ Orchestrator│
│  (FastAPI)  │     │              │     │   Worker    │
└─────────────┘     └──────────────┘     └──────┬──────┘
       │                     │                   │
       │                     │                   │ Creates
       ▼                     ▼                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ PostgreSQL  │◀────│   Metrics    │◀────│  K8s Jobs   │
│  (metrics)  │     │  Collector   │     │  (Training) │
└─────────────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  Dashboard  │
│  (React)    │
└─────────────┘
```

## Features

| Component | Technology |
|-----------|------------|
| **Job Submission** | REST API → Redis Queue → Async Workers |
| **Orchestration** | Kubernetes Jobs (each training run = 1 K8s Job) |
| **Distributed Training** | PyTorch DDP (simulated multi-worker) |
| **Metrics & Logging** | Redis → PostgreSQL → Dashboard |
| **CI/CD** | GitHub Actions → Docker Registry → K8s Deploy |

## Quick Start

### Local Development (Docker Compose)

```bash
# Install deps (from repo root)
make install

# Start Redis + Postgres
make infra

# Terminal 1: Backend (PYTHONPATH includes shared)
make backend

# Terminal 2: Orchestrator worker
make orchestrator

# Terminal 3: Dashboard
make dashboard

# Submit a job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"training_config":{"epochs":2,"batch_size":32}}'
```

Without K8s, the orchestrator logs "Would create K8s Job" (set `USE_K8S=true` with a real cluster). To test training locally: `make trainer`.

### Kubernetes Deployment

```bash
# Apply base infrastructure
kubectl apply -f k8s/base/

# Deploy backend + orchestrator
kubectl apply -f k8s/backend/
```

## Project Structure

```
├── backend/           # FastAPI REST API, job submission
├── orchestrator/      # Celery worker, Redis → K8s Job creation
├── trainer/           # Training code (Docker image for K8s)
├── dashboard/         # React metrics dashboard
├── k8s/               # Kubernetes manifests
├── .github/workflows/ # CI/CD pipelines
└── docker-compose.yml # Local dev infrastructure
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs` | Submit training job |
| GET | `/api/v1/jobs` | List all jobs |
| GET | `/api/v1/jobs/{id}` | Get job details + metrics |
| GET | `/api/v1/jobs/{id}/logs` | Stream training logs |
| DELETE | `/api/v1/jobs/{id}` | Cancel job |

## Job Config Example

```json
{
  "model_config": {
    "architecture": "resnet18",
    "num_classes": 10
  },
  "training_config": {
    "epochs": 10,
    "batch_size": 32,
    "learning_rate": 0.001,
    "world_size": 2
  },
  "dataset": "cifar10"
}
```

`world_size` > 1 enables simulated multi-GPU / DDP training (PyTorch DistributedDataParallel).

## License

MIT
