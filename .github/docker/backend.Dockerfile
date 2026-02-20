# Build from repo root: docker build -f .github/docker/backend.Dockerfile .
FROM python:3.11-slim

WORKDIR /app

# Copy shared and backend
COPY shared/ /app/shared/
COPY backend/ /app/backend/

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/backend:/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
