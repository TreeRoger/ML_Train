# ADR 0003: Simulated DDP before real multi-GPU cluster

## Status
Accepted

## Context
The platform needs distributed training semantics, but early stage should not depend on owning a real GPU cluster.

## Decision
Support PyTorch DDP simulation locally / CPU-first, then upgrade to GPU-backed execution.

## Why
- Faster dev loop.
- Lets us validate orchestration and metric plumbing first.
- Reduces infra cost during iteration.

## Consequences
- Throughput claims are not production GPU numbers yet.
- Need a later benchmark pass on real hardware.
