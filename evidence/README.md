# Evidence Checklist

Use this folder to keep proof that the system runs end-to-end.

## What to capture
- `screenshots/dashboard-running.png`: active job with loss/accuracy chart.
- `screenshots/jobs-list.png`: multiple jobs with different statuses.
- `logs/backend-startup.log`: backend startup + health check.
- `logs/orchestrator-job-lifecycle.log`: queued -> running -> succeeded flow.
- `logs/trainer-metrics.log`: trainer metric publish samples.

## Suggested capture flow
1. Start infra and all services locally.
2. Submit 2-3 jobs with different `world_size` and `epochs`.
3. Save dashboard screenshots while metrics update.
4. Save terminal logs for backend/orchestrator/trainer.

Keeping this evidence up to date makes the project feel real and easier to explain in interviews.
