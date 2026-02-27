# ADR 0002: One Kubernetes Job per training run

## Status
Accepted

## Context
Each user submission should have isolated runtime, retries, and lifecycle.

## Decision
Map one training request to one Kubernetes `Job`.

## Why
- Clean run boundaries.
- Native retry/ttl semantics.
- Easy to reason about cost and cleanup.

## Consequences
- Startup overhead per run.
- Need template management/versioning discipline.
