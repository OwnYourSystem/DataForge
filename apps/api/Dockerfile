# Build context: the repository root.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --create-home app
WORKDIR /srv/apps/api
COPY apps/api/pyproject.toml ./
COPY apps/api/dataforge ./dataforge
# .dockerignore keeps the reference solutions out of the image.
COPY curriculum /srv/curriculum
ENV DF_CURRICULUM_DIR=/srv/curriculum

# Control plane. dbt is not installed here.
FROM base AS api
RUN pip install --no-cache-dir .
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "dataforge.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# Execution plane. Runs dbt for learner code. It has no HTTP port.
FROM base AS worker
# Use WORKER_EXTRAS=worker,databricks for the Databricks backend.
ARG WORKER_EXTRAS=worker
RUN pip install --no-cache-dir ".[${WORKER_EXTRAS}]"
USER 10001:10001
CMD ["python", "-m", "dataforge.worker"]
