# Portfolio demo script

## Five-minute version

1. Show the problem and state that all data is synthetic.
2. Run the generator and point to the event schema and validation report.
3. Train the model and show the immutable version plus metrics.
4. Open the API request/response and point out model version, decision, and request ID.
5. Render the Kubernetes overlay and explain probes, non-root execution, resources, HPA, and NetworkPolicy.
6. Show the drift thresholds and rollback runbook.

## Fifteen-minute version

1. Start with the architecture diagram.
2. Demonstrate a valid and invalid transaction at the domain boundary.
3. Show the shared feature schema used by offline and online paths.
4. Compare the NumPy baseline with one optional framework adapter.
5. Explain why registration and promotion are separate operations.
6. Walk through Kafka, Spark, Airflow, Kubeflow, and DVC as interchangeable orchestration/data-plane adapters.
7. Show Prometheus/Grafana and the optional ELK profile.
8. Finish with threat model, retention, pseudonymization, model drift, and the learning plan.

## Strong interview statements

- “The feature transformer is versioned and shared by training and serving, so offline/online skew is an explicit failure mode.”
- “A registered model is immutable; promotion only changes a champion pointer, which makes rollback auditable.”
- “Readiness is false until the model artifact can be loaded, so Kubernetes does not route traffic to a cold or broken pod.”
- “The local path is intentionally CPU-only; GPU and TPU are deployment profiles selected after measuring the workload.”
- “I separate the canonical implementation from provider adapters so I can move between local, AWS, GCP, and Azure without changing the domain contract.”

