# Free single-container test deployment: web app, API, and worker in one
# container. dbt IS in this image, so learner SQL runs in the same container
# as the API. Use it only for a test with learners you trust.
# For the split layout (worker in its own service), use split.Dockerfile and
# blueprint-split.yaml in this directory.
# Build context: the repository root.
FROM node:22-slim AS web
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NODE_ENV=production
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --create-home app
COPY --from=web /usr/local/bin/node /usr/local/bin/node

WORKDIR /srv/apps/api
COPY apps/api/pyproject.toml ./
COPY apps/api/dataforge ./dataforge
RUN pip install --no-cache-dir ".[worker]"
# .dockerignore keeps the reference solutions out of the image.
COPY curriculum /srv/curriculum
ENV DF_CURRICULUM_DIR=/srv/curriculum

WORKDIR /srv/web
COPY --from=web /app/.next/standalone ./
COPY --from=web /app/.next/static ./.next/static
COPY deploy/render/start.sh /srv/start.sh

USER 10001:10001
# The free plan has 512 MB. Keep the web server small so that dbt has room.
ENV API_INTERNAL_URL=http://127.0.0.1:8000 HOSTNAME=0.0.0.0 \
    DF_RUN_WORKER=1 NODE_OPTIONS=--max-old-space-size=160
EXPOSE 3000
CMD ["bash", "/srv/start.sh"]
