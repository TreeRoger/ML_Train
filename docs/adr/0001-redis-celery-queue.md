# ADR 0001: Redis + Celery for async queue

## Status
Accepted

## Context
The first goal was to decouple API submission latency from training startup. We needed fast local iteration and simple operations.

## Decision
Use Redis as broker + Celery worker for asynchronous job handoff.

## Why
- Quick local setup for demos and iteration.
- Good enough reliability for this stage.
- Straight path to queue-backed orchestration semantics.

## Consequences
- Redis is a single point unless operated HA.
- If workload grows, RabbitMQ/Kafka could be better fits.
