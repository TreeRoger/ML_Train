.PHONY: dev infra backend orchestrator trainer dashboard test

# Start Redis + Postgres
infra:
	docker-compose up -d redis postgres

# Run backend (requires: make infra, or set DATABASE_URL=sqlite+aiosqlite:///./ml_train.db for DB-only dev)
backend:
	cd backend && PYTHONPATH=.:.. uvicorn app.main:app --reload --host 0.0.0.0

# Run orchestrator worker (requires: make infra)
orchestrator:
	cd orchestrator && celery -A app.celery_app worker -l info

# Run training locally (standalone, no K8s). Works without Redis (metrics skipped).
trainer:
	cd trainer && python -m training.main --job-id dev-123 --config '{"model_config":{"architecture":"resnet18","num_classes":10},"training_config":{"epochs":2,"batch_size":32}}'

# Run dashboard
dashboard:
	cd dashboard && npm run dev

# Install all deps
install:
	pip install -r backend/requirements.txt
	pip install -r orchestrator/requirements.txt
	pip install -r trainer/requirements.txt
	cd dashboard && npm install

# Quick test: backend health
test:
	curl -s http://localhost:8000/health | head -1
