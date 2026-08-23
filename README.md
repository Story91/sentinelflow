# SentinelFlow

**Production Real-Time Risk Scoring Platform**

SentinelFlow to projekt pokazowy AI/MLOps zbudowany wokół realistycznego problemu: oceny ryzyka transakcji w czasie rzeczywistym. Dane są syntetyczne, lokalny wariant jest wykonywalny, a manifesty chmurowe pokazują granice integracji bez udawania aktywnego wdrożenia.

Projekt pokazuje pełny cykl życia modelu:

```text
synthetic events -> validation/ETL -> feature contract -> training/evaluation
       -> model registry -> HTTP serving -> Kafka/Spark integration
       -> Kubernetes/CI-CD -> metrics, logs, drift, retraining and rollback
```

## Co jest działające już lokalnie

- deterministyczny generator transakcji bez danych osobowych,
- walidacja kontraktu danych na granicy systemu,
- wersjonowany feature engineering współdzielony przez trening i serving,
- trening modelu oraz metryki klasyfikacji,
- niezmienny, plikowy registry z promocją modelu `champion`,
- API FastAPI z liveness/readiness, predykcją i metrykami Prometheus,
- testy jednostkowe, kontraktowe i smoke testy HTTP,
- drift PSI, pseudonimizacja HMAC i reguły retencji,
- wykonywalne definicje Airflow, Kubeflow, Spark, Kafka, Docker, Kubernetes i CI/CD,
- opcjonalne profile MLflow oraz Elasticsearch/Logstash/Kibana.

## Szybki start

Wymagany jest Python 3.12+.

```powershell
cd sentinelflow
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[quality]"

python -m sentinelflow.cli generate --output data/raw/transactions.csv --rows 5000 --seed 42
python -m sentinelflow.cli train --data data/raw/transactions.csv --registry model-registry
pytest
ruff check src tests scripts pipelines
mypy src
```

Uruchomienie API:

```powershell
$env:SENTINELFLOW_MODEL_REGISTRY = "./model-registry"
uvicorn sentinelflow.api.app:app --host 0.0.0.0 --port 8000
```

## Docker Compose — pełny lokalny profil

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
python scripts/docker_smoke.py
docker compose -f infra/docker/docker-compose.yml ps -a
```

Stos sam generuje dane, trenuje model, promuje wersję `champion`, a dopiero potem uruchamia API. Dostępne adresy:

| Usługa | Adres |
|---|---|
| API / OpenAPI | `http://localhost:8000/docs` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3001` |
| MinIO API / konsola | `http://localhost:9000` / `http://localhost:9001` |
| Kafka / Redpanda | `localhost:9092` |
| Postgres | `localhost:5432` |

Port Grafany można zmienić przez `GRAFANA_PORT`. Profil ELK rozszerza ten sam stos:

```powershell
docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.elk.yml up -d --wait
```

Kibana jest wtedy dostępna pod `http://localhost:5601`, a Elasticsearch pod `http://localhost:9200`.

MLflow ma osobny profil w `infra/mlflow/`, ponieważ jego storage i cykl życia nie powinny być ukryte w kontenerze API. Dokładne polecenia znajdują się w [`infra/mlflow/README.md`](infra/mlflow/README.md).

Przykładowe zapytanie:

```powershell
Invoke-RestMethod http://localhost:8000/v1/risk-score -Method Post -ContentType 'application/json' -Body (@{
  transaction_id = 'txn_demo_001'
  customer_id = 'cust_demo_001'
  event_time = '2026-01-15T02:30:00Z'
  amount = 1800.00
  currency = 'PLN'
  merchant_category = 'electronics'
  country = 'PL'
  device_trust_score = 0.12
  account_age_days = 12
  is_new_device = $true
  velocity_1h = 9
  distance_km = 850
  chargeback_history = 1
} | ConvertTo-Json)
```

Raport driftu dla dwóch wsadów:

```powershell
sentinelflow monitor --reference data/reference.csv --current data/current.csv --output data/reports/drift.json
```

Polecenie kończy się kodem `2`, gdy wykryje drift krytyczny, dzięki czemu może blokować automatyczną promocję w CI lub orkiestratorze.

## Lokalny Kubernetes

Overlay lokalny nie wymaga CRD Prometheus Operatora i sam uruchamia jednorazowy Job treningowy:

```powershell
docker build -f infra/docker/Dockerfile -t sentinelflow-api:local .
kubectl apply -k infra/kubernetes/overlays/local
kubectl -n sentinelflow wait --for=condition=complete job/sentinelflow-bootstrap-model --timeout=180s
kubectl -n sentinelflow rollout status deployment/sentinelflow-api --timeout=180s
kubectl -n sentinelflow port-forward service/sentinelflow-api 8000:80
```

Docker Desktop Kubernetes korzysta z tego samego lokalnego obrazu. Dla `kind` lub `minikube` trzeba najpierw załadować obraz do klastra. HPA wymaga Metrics Server, a bazowy `ServiceMonitor` — Prometheus Operatora; te zależności są przeznaczone dla klastra platformowego.

## Struktura

```text
src/sentinelflow/       kod domeny, danych, ML, API i security
tests/                   testy kontraktów, cech, modelu i prywatności
pipelines/               Airflow, Kubeflow, Spark i Kafka
infra/                   Docker, Kubernetes, monitoring i Terraform
configs/                 jawna konfiguracja aplikacji i modelu
sql/                     schemat danych oraz zapytania operacyjne
docs/                    architektura, threat model, runbook i ścieżka nauki
```

## Zasady projektu

1. **Jedna ścieżka referencyjna, wiele adapterów.** Lokalny happy path używa NumPy, żeby był uruchamialny bez GPU i bez konta cloud. Scikit-learn, XGBoost, PyTorch, TensorFlow/Keras, MLflow, Kubeflow, SageMaker, Vertex AI i Azure ML są osobnymi, sensownymi wariantami — nie ozdobnikami w jednym monolicie.
2. **Kontrakty przed frameworkami.** Schemat transakcji, feature schema, model metadata, health checks i metryki mają stabilne kontrakty niezależnie od adaptera.
3. **Bezpieczny default.** Brak prawdziwych PII, sekrety wyłącznie przez środowisko/secret manager, obrazy bez roota, domyślna retencja i audyt.
4. **Operacyjność jest częścią funkcji.** Każdy model ma fingerprint danych, metryki, wersję, próg decyzyjny i ścieżkę rollbacku.

## Mapa wymagań stanowiska

| Wymaganie | Artefakt w projekcie |
|---|---|
| Python, SQL, scripting | `src/`, `sql/`, `scripts/` |
| ML i walidacja | `src/sentinelflow/ml/`, `tests/` |
| Kafka, Spark, ETL | `pipelines/kafka/`, `pipelines/spark/`, `src/sentinelflow/data/` |
| MLflow, Airflow, Kubeflow, DVC | `pipelines/`, `dvc.yaml`, `infra/mlflow/` |
| Docker, Kubernetes | `infra/docker/`, `infra/kubernetes/` |
| CI/CD | `.github/workflows/ci.yml` |
| Prometheus, Grafana, ELK | `infra/monitoring/` |
| AWS, SageMaker, GCP, Azure ML | `infra/cloud/` |
| drift, reliability, retraining | `src/sentinelflow/ml/drift.py`, `docs/runbook.md` |
| GDPR, CCPA, security, ethics | `src/sentinelflow/security/`, `docs/security-and-compliance.md` |

## Granica gotowości

Rdzeń lokalny, Docker Compose, MLflow, ELK i kompilacja Kubeflow są testowalne bez kont chmurowych. AWS, Azure ML, Vertex AI i SageMaker pozostają bezpiecznymi szablonami: przed wdrożeniem wymagają własnych identyfikatorów, IAM, sieci, rejestru obrazów, budżetu i sekretów. Szczegóły są w [`docs/manual-steps.md`](docs/manual-steps.md).

Obraz treningowy SageMaker ma osobny target, aby nie mieszać kontraktu platformy z procesem API:

```powershell
docker build --target sagemaker-training -f infra/docker/Dockerfile -t sentinelflow-sagemaker:local .
```
