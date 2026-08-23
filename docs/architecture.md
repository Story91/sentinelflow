# Architecture

## Reference flow

```text
                    +-------------------+
                    | upstream systems  |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Kafka / Redpanda  |  raw event stream
                    +---------+---------+
                              |
                +-------------+-------------+
                |                           |
                v                           v
       +----------------+          +------------------+
       | Spark Streaming|          | object storage   |
       | validation/ETL |          | raw + features   |
       +--------+-------+          +------------------+
                |
                v
       +----------------+       +-------------------+
       | Risk API       |<------| model registry    |
       | FastAPI        |       | MLflow/local      |
       +--------+-------+       +-------------------+
                |
                v
       +----------------+       +-------------------+
       | business app   |       | Prometheus/Grafana|
       | approve/review |       | ELK + drift jobs  |
       +----------------+       +-------------------+
```

## Boundaries

- `domain`: business invariants and schema; no infrastructure imports.
- `data`: ingestion, validation and deterministic features.
- `ml`: training, evaluation, registry and drift; no HTTP concerns.
- `api`: transport and request/response handling; delegates to `RiskScoringService`.
- `pipelines`: orchestration adapters; commands remain reusable outside orchestrators.
- `infra`: deployment concerns only; secrets are injected at runtime.

## Model lifecycle

1. A data quality job validates the incoming batch and writes a report.
2. Training uses the exact feature transformer used by serving.
3. Evaluation produces quality metrics and a data fingerprint.
4. A model is registered immutably.
5. Promotion changes only the champion pointer after quality gates pass.
6. Serving exposes model version in every prediction response.
7. Monitoring tracks latency, errors, input quality, drift, and delayed labels.
8. Retraining is triggered by schedule, drift, or performance degradation.

## Local versus cloud

The local implementation uses a filesystem registry and NumPy model for fast, deterministic learning. The production base manifest requests RWX storage because multiple serving replicas may run on different nodes; the one-node local overlay patches this to RWO. A real cloud deployment should prefer an object-backed model registry or an RWX CSI driver with explicit backup and access controls.

AWS is the primary cloud track: S3 for artifacts, ECR for images, EKS for serving, and SageMaker for managed training. `infra/cloud/gcp` and `infra/cloud/azure` show the equivalent job contracts without pretending that credentials or a live account exist in the repository.
