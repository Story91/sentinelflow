FROM python:3.12-slim AS base

ARG SENTINELFLOW_EXTRAS=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app

COPY pyproject.toml README.md ./
COPY src ./src
RUN if [ -n "${SENTINELFLOW_EXTRAS}" ]; then \
      pip install --no-cache-dir ".[${SENTINELFLOW_EXTRAS}]"; \
    else \
      pip install --no-cache-dir .; \
    fi

COPY configs ./configs
RUN mkdir -p /app/model-registry /app/data /app/logs && chown -R app:app /app

USER 10001:10001

FROM base AS sagemaker-training

USER root
RUN mkdir -p /opt/ml/input/data/train /opt/ml/model && chown -R app:app /opt/ml
USER 10001:10001

ENTRYPOINT ["sentinelflow-sagemaker"]
CMD ["train"]

FROM base AS runtime

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["uvicorn", "sentinelflow.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
