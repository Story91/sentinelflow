# Security, privacy, and compliance

This is an engineering study project, not legal advice. The controls below are implementation targets that should be reviewed against the organisation's legal basis, data-processing agreements, and security standards.

## Data minimisation

- The repository uses synthetic data only.
- The online contract contains no name, email, card number, address, or raw device identifier.
- Customer identifiers must be tokenized before entering the scoring boundary.
- Logs should contain request IDs and model versions, never raw customer identifiers.

## GDPR/CCPA-oriented controls

- purpose limitation: risk scoring only;
- retention: configurable TTL with an explicit cutoff helper;
- deletion: remove raw events, derived features, and audit references for a subject token;
- access: restrict training data and registry buckets using least-privilege roles;
- auditability: retain model version, feature schema version, data fingerprint, and decision timestamp;
- explainability: expose reason codes in a future policy layer; do not treat the probability as a legal decision explanation;
- data-subject requests: maintain a deletion workflow and processing inventory outside the model code.

## Threat model summary

| Threat | Control |
|---|---|
| Poisoned training data | schema validation, data quality gates, dataset fingerprint, review before promotion |
| Model artifact tampering | immutable versions, SHA-256 verification before load, restricted registry write access |
| Secret leakage | environment/secret manager injection, `.env` ignored, no credentials in manifests |
| Abuse of prediction API | strict local request schema and audit IDs; authentication, rate limits, TLS and body limits are mandatory ingress controls before external exposure |
| PII in logs | structured redaction and pseudonymization before logging |
| Supply-chain issue | pinned dependency ranges, image scanning in CI, non-root image |
| Bad rollout | readiness checks, canary/rollback procedure, model version in responses |
