FROM mcr.microsoft.com/devcontainers/python:3.10-bookworm

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    libpq-dev \
    git

COPY requirements.txt requirements-dev.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements-dev.txt \
    && pip install --no-cache-dir pre-commit

# Asume que el WORKDIR se monta con el código del host (incluyendo .pre-commit-config.yaml)
WORKDIR /workspaces/vehicle_event_microservice

# Intenta instalar hooks (no fallar si aún no hay .git o .pre-commit-config.yaml)
RUN pre-commit install --install-hooks || true

ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV PYTHONUNBUFFERED=1
