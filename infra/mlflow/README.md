# Local MLflow profile

MLflow runs separately from the serving API and stores its SQLite database and proxied artifacts in the persistent `mlflow-data` volume.

Start the server from the project root:

```powershell
docker compose -f infra/mlflow/docker-compose.yml up -d --wait
```

For a host-based training run, install the dedicated tracking extra:

```powershell
python -m pip install -e ".[tracking]"
sentinelflow train --data data/raw/transactions.csv --registry model-registry --mlflow-tracking-uri http://localhost:5000
```

For an isolated container run, build the training image and use the Compose network:

```powershell
docker build -f infra/docker/Dockerfile --build-arg SENTINELFLOW_EXTRAS=tracking -t sentinelflow-training:local .
docker run --rm --network mlflow_default -e GIT_PYTHON_REFRESH=quiet -w /tmp sentinelflow-training:local sh -c "mkdir -p /tmp/training && sentinelflow generate --output /tmp/training/transactions.csv --rows 5000 --seed 42 && sentinelflow train --data /tmp/training/transactions.csv --registry /tmp/training/model-registry --mlflow-tracking-uri http://mlflow:5000"
```

Open `http://localhost:5000`. A successful run contains the quality metrics, training parameters, `metadata.json`, and `model.npz`. The filesystem registry remains the deterministic serving and rollback contract for the local demo.
