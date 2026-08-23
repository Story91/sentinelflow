# What the owner must still do

The executable local path is complete. The following actions require the owner's machine settings, identity, accounts, or deployment decisions and are intentionally not automated:

1. Enable Kubernetes in Docker Desktop and select its `docker-desktop` context if you want to run the local Kustomize overlay. The rendered overlay is valid without Prometheus Operator; HPA metrics require Metrics Server.
2. Create or connect a Git repository and configure branch protection, image registry access, CI environments, and deployment secrets.
3. Decide whether to use AWS, GCP, or Azure for a live deployment; create the account, budget alerts, IAM roles, private networking, KMS keys, and registries.
   For SageMaker, publish the dedicated training target with
   `docker build --target sagemaker-training -f infra/docker/Dockerfile -t <ecr-image> .`.
   Azure ML binds the declared `model_registry` output, while Vertex AI uses its `/gcs/<bucket>`
   Cloud Storage mount; keep those paths aligned with your selected bucket and datastore.
4. Replace every `REPLACE_ME`, `ACCOUNT_ID`, `PROJECT_ID`, and `ghcr.io/example` value before any cloud command.
5. Replace local-only passwords and the default Grafana administrator credentials before exposing any port outside localhost.
6. Run a real deployment only after reviewing cost, TLS, authentication, rate limits, backup/restore, incident response, and data-processing requirements.
7. Add a real legal review and organisation-specific GDPR/CCPA records if the synthetic demo becomes a real product.
8. Learn and explain the code, trade-offs, incidents, and interview statements; the project is evidence, not a substitute for experience.
9. Pursue any certification or formal education requested by a specific employer.

No real credentials, payment data, or personal data belong in this repository.
