FROM python:3.11-slim

WORKDIR /app

# Install system deps for torch (optional, for CPU)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY training/ training/

ENV PYTHONPATH=/app
ENV REDIS_URL=redis://redis:6379/0

ENTRYPOINT ["python", "-m", "training.main"]
