# Distributed ML Training Orchestrator

> Mini Tesla-style ML platform for queueing, orchestration, and observability.

This project is intentionally built as an infra-heavy ML training system, not just an experiment tracker. A training request enters through an API, gets queued, is picked by an orchestrator, scheduled as a Kubernetes Job, and streams metrics to storage and dashboard.

## Architecture

```
REST API (FastAPI)
  -> Redis queue
    -> Orchestrator worker (Celery)
      -> Kubernetes Job (trainer container)
        -> Redis pub/sub metrics
          -> Metrics collector
            -> PostgreSQL
              -> Dashboard (React)
```

## What It Does

- Submit training jobs asynchronously with API + Redis queue.
- Schedule each training run as a Kubernetes Job.
- Simulate distributed/multi-worker training with PyTorch DDP.
- Persist metrics and surface them in a dashboard.
- Build/test/deploy with GitHub Actions CI/CD.

## Local Quick Start

```bash
make install
make infra
```

Run in separate terminals:

```bash
make backend
make orchestrator
make dashboard
```

**Without Docker:** Use SQLite for the DB (`DATABASE_URL=sqlite+aiosqlite:///./ml_train.db`) and run Redis locally (`brew install redis && redis-server`). The trainer runs without Redis (metrics publishing is skipped).

Submit a job:

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model_config": {"architecture": "resnet18", "num_classes": 10},
    "training_config": {"epochs": 2, "batch_size": 32, "world_size": 2}
  }'
```

## Opinionated Defaults (On Purpose)

- Single namespace default: `ml-train`.
- Job TTL after finish: 1 hour.
- Simulated `world_size` capped to 8.
- Redis used for both queueing and real-time metric fanout.

## Real Tradeoffs / What Is Intentionally Not Done Yet

- No auth/RBAC on API endpoints yet.
- No durable centralized log store yet (metrics are centralized; logs are partial).
- No retry policy tuning for failed long jobs beyond basic K8s `backoffLimit`.
- No model artifact registry hookup yet.
- No autoscaling policy tuning per dataset/model size yet.

## Human Engineering Notes

- ADRs (decision records): see `docs/adr/`.
- Failure log and fixes: see `docs/pitfalls.md`.
- Personal roadmap: see `docs/roadmap.md`.
- Evidence checklist and capture plan: see `evidence/README.md`.

## Targeted Regression Tests

The backend CI now includes a focused regression test for a real bug we hit:

- `backend/tests/test_job_schema_alias.py`
  - Guards against Pydantic v2 alias/reserved-name regressions around `model_config`.

## API

- `POST /api/v1/jobs` submit a training job.
- `GET /api/v1/jobs` list jobs.
- `GET /api/v1/jobs/{id}` get job details.
- `GET /api/v1/jobs/{id}/metrics` get metric series.

## License

MIT
