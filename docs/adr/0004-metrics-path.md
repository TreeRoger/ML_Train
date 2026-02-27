# ADR 0004: Redis pub/sub to PostgreSQL metrics sink

## Status
Accepted

## Context
Metrics should be visible in near real time and also queryable historically.

## Decision
Trainer publishes metric events to Redis pub/sub, collector writes durable rows to PostgreSQL.

## Why
- Real-time fanout plus durable storage.
- Simple implementation for current scope.

## Consequences
- Pub/sub is best-effort; some events can be lost under faults.
- Future: move to streams/event log for stronger guarantees.
