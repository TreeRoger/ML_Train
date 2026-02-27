# Personal Roadmap

## Next 1-2 weekends
- Add explicit job cancel semantics (`DELETE /jobs/{id}` with worker-side stop flow).
- Add SSE endpoint for live training logs per job.
- Add basic auth for API and dashboard read endpoints.

## Near-term production hardening
- Move metrics transport from pub/sub to Redis Streams (replay support).
- Add retry/backoff and dead-letter handling for orchestration failures.
- Add namespace/resource quotas per environment.

## Later
- Integrate artifact/model registry.
- Add autoscaling policy experiments for mixed workloads.
- Add benchmark report on real GPU hardware.
