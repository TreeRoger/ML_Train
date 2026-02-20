"""Celery tasks: consume from queue, create K8s Jobs."""

import json
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import redis

from orchestrator.app.celery_app import app, settings

logger = logging.getLogger(__name__)


def _get_k8s_client():
    """Load K8s config (in-cluster or kubeconfig)."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            raise RuntimeError("Could not load Kubernetes config")
    return client.BatchV1Api(), client.CoreV1Api()


def _update_redis_status(job_id: str, status: str, **extra):
    r = redis.from_url(settings.redis_url, decode_responses=True)
    key = f"ml_train:job_status:{job_id}"
    data = {"status": status, **extra}
    r.setex(key, 86400, json.dumps(data))
    r.close()


@app.task(bind=True, name="orchestrator.tasks.process_training_job")
def process_training_job(self, job_id: str, payload: dict | None = None):
    """
    Process a queued training job: create K8s Job, poll until complete.
    """
    if not payload:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        data = r.get(f"ml_train:job:{job_id}")
        r.close()
        if not data:
            logger.error(f"Job {job_id} not found in Redis")
            return {"status": "failed", "error": "job not found"}
        payload = json.loads(data)

    _update_redis_status(job_id, "pending")

    if not settings.use_k8s:
        logger.info(f"[DEV] Would create K8s Job for {job_id}. Set USE_K8S=true for real runs.")
        _update_redis_status(job_id, "succeeded", k8s_job_name="(simulated)")
        return {"status": "succeeded", "job_id": job_id}

    try:
        batch_api, core_api = _get_k8s_client()
    except Exception as e:
        logger.exception("K8s client init failed")
        _update_redis_status(job_id, "failed", error=str(e))
        return {"status": "failed", "error": str(e)}

    k8s_job_name = f"ml-train-{job_id[:8]}"
    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": k8s_job_name,
            "namespace": settings.namespace,
        },
        "spec": {
            "ttlSecondsAfterFinished": 3600,
            "backoffLimit": 2,
            "template": {
                "spec": {
                    "restartPolicy": "OnFailure",
                    "containers": [
                        {
                            "name": "trainer",
                            "image": settings.trainer_image,
                            "command": ["python", "-m", "training.main"],
                            "args": [
                                "--job-id", job_id,
                                "--config", json.dumps(payload),
                            ],
                            "env": [
                                {"name": "REDIS_URL", "value": f"redis://redis.{settings.namespace}.svc.cluster.local:6379/0"},
                            ],
                            "resources": {
                                "requests": {"memory": "2Gi", "cpu": "1"},
                                "limits": {"memory": "4Gi", "cpu": "2"},
                            },
                        }
                    ],
                }
            },
        },
    }

    try:
        batch_api.create_namespaced_job(
            namespace=settings.namespace,
            body=job_manifest,
        )
        _update_redis_status(job_id, "running", k8s_job_name=k8s_job_name)
        logger.info(f"Created K8s Job {k8s_job_name} for {job_id}")
    except ApiException as e:
        logger.exception(f"Failed to create K8s Job: {e}")
        _update_redis_status(job_id, "failed", error=str(e.body))
        return {"status": "failed", "error": str(e.body)}

    # Poll for completion
    import time
    for _ in range(7200):  # ~2 hours max
        time.sleep(5)
        try:
            job = batch_api.read_namespaced_job(k8s_job_name, settings.namespace)
            if job.status.succeeded:
                _update_redis_status(job_id, "succeeded", k8s_job_name=k8s_job_name)
                return {"status": "succeeded", "job_id": job_id}
            if job.status.failed:
                _update_redis_status(job_id, "failed", k8s_job_name=k8s_job_name)
                return {"status": "failed", "job_id": job_id}
        except ApiException:
            pass

    _update_redis_status(job_id, "failed", error="timeout")
    return {"status": "failed", "error": "timeout"}
