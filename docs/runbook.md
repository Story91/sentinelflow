# Operations runbook

## Health checks

- `/health/live` confirms the process is alive.
- `/health/ready` confirms a champion model can be loaded.
- `/metrics` exposes request counters and decision counts.
- Prometheus `/api/v1/targets` must report `sentinelflow-api` as `up`.
- `python scripts/docker_smoke.py` verifies API, prediction, Prometheus, Grafana, and MinIO together.

For the local stack:

```powershell
docker compose -f infra/docker/docker-compose.yml ps -a
docker compose -f infra/docker/docker-compose.yml logs --tail=100 trainer api prometheus
```

The trainer is expected to finish with exit code `0`; it is a one-shot bootstrap job, not a long-running service.

## Rollback

1. Identify the last healthy model version from the registry and dashboard.
2. Promote that immutable version as champion.
3. Restart or reload serving pods if the deployment does not hot-reload the pointer.
4. Confirm readiness and run the smoke request.
5. Record the incident, model version, data fingerprint, and remediation.

## Drift response

| Signal | Action |
|---|---|
| PSI < 0.10 | observe |
| 0.10 <= PSI < 0.25 | investigate segments and upstream changes |
| PSI >= 0.25 | block automatic promotion and start retraining investigation |
| Recall below gate | review delayed labels, threshold, and feature freshness |
| API error/latency SLO breach | rollback deployment and inspect saturation/dependencies |

Create the same report used by the scheduled Airflow DAG:

```powershell
sentinelflow monitor --reference data/reference.csv --current data/current.csv --output data/reports/drift.json
```

Exit code `2` means critical drift and should stop automatic promotion.

## Reliability defaults

- Kafka consumers must be idempotent and use a dead-letter topic.
- External calls require bounded timeouts and retries with backoff.
- Model loading happens before readiness becomes healthy.
- Model artifacts are SHA-256 verified before loading.
- The API is stateless; model artifacts are versioned outside the container.
- Resource requests and limits are explicit in Kubernetes manifests.
