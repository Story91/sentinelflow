# Requirements matrix

This matrix translates the job description into evidence that can be shown in the repository and discussed during an interview.

| Job requirement | Evidence | How to practise |
|---|---|---|
| Scalable train/validate/deploy/monitor pipelines | pipelines/, src/sentinelflow/ml/training.py, infra/ | Run the local path, then explain where each stage moves in production |
| Data and training automation | CLI, DVC, Airflow DAG, Kubeflow pipeline | Change the seed or input contract and observe the pipeline failure |
| Model integration with applications | FastAPI app and RiskScoringService | Send a request and trace model version to response |
| Data drift and model drift | ml/drift.py, ml/drift_report.py, monitor CLI, Airflow drift DAG | Compare reference/current batches and delayed-label metrics |
| CPU/GPU/TPU optimisation | compute profiles and GPU patch | Explain why this tabular serving model stays on CPU |
| Docker and Kubernetes | Dockerfile, Compose, Kustomize, HPA, probes, NetworkPolicy | Build the image, render manifests, inspect security context |
| CI/CD | GitHub Actions workflow | Explain quality gate, image build, scan, and deployment boundary |
| Performance, reliability, resilience | timeouts, readiness, HPA, immutable registry, rollback runbook | Kill the model or dependency and describe expected readiness behavior |
| Security, privacy, ethics | privacy helpers, SQL token field, threat model, compliance doc | Identify what data is intentionally absent and why |
| Collaboration with DS, DE, dev, security | architecture boundaries, contracts, ADR-style docs | Present ownership of domain, data, ML, API, and platform layers |
| Python, SQL, scripting | src/, sql/, PowerShell smoke script | Rewrite one boundary rule and add its test |
| TensorFlow, PyTorch, Scikit-learn, Keras, XGBoost | optional framework adapters | Compare latency, quality, artifact format, and operational trade-offs |
| MLflow, Kubeflow, Airflow, DVC | adapters and pipeline definitions | Run local registry first, then map the same contract to each tool |
| Public cloud | AWS Terraform/SageMaker plus GCP/Azure job contracts | Explain storage, IAM, image registry, compute, and private networking |
| Spark, Kafka, ETL | streaming job, producer/consumer adapters, Kafka smoke script | Run producer-to-consumer smoke, then explain partitions, watermarking, retries, and DLQ |
| Prometheus, Grafana, ELK | metrics endpoint, dashboard, alerts, Logstash profile | Relate a metric, a dashboard panel, an alert, and an operator action |
| GDPR and CCPA | retention, pseudonymization, deletion/audit guidance | Explain minimisation, purpose limitation, access, and deletion workflow |

The project does not claim that a static manifest equals a live cloud deployment. A live deployment requires credentials, account setup, network policy, and an explicit cost decision by the owner.
