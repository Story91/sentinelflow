# Learning path

The project is designed to be learned in vertical slices.

1. **Python/domain:** schemas, validation errors, dataclasses, typing, tests.
2. **SQL/data:** event schema, indexes, ETL invariants, late and invalid events.
3. **ML fundamentals:** features, train/test split, precision/recall, ROC-AUC, threshold trade-offs.
4. **MLOps:** model metadata, registry, promotion, reproducibility, DVC and MLflow.
5. **Serving:** FastAPI contracts, health checks, timeout budgets, structured logs.
6. **Streaming:** Kafka semantics, partitioning, consumer groups, retries and DLQ.
7. **Big Data:** Spark transformations, checkpointing, watermarking and exactly-once trade-offs.
8. **Containers/platform:** Docker layers, Kubernetes probes, resources, HPA, RBAC and NetworkPolicy.
9. **Observability:** Prometheus metrics, Grafana panels, ELK logs, drift and alert design.
10. **Cloud/security:** IAM, artifact storage, managed training, private networking, GDPR/CCPA controls.

For every slice, the intended study loop is: read the module, run its test, break one invariant deliberately, observe the failure, then explain the design in interview language.

