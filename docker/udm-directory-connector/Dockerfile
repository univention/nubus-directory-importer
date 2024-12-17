# syntax=docker/dockerfile:1.9
# Inspired by: https://hynek.me/articles/docker-uv/

ARG UCS_BASE_IMAGE_TAG=0.14.0-build-2024-12-12
ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-520

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS build
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

COPY --from=ghcr.io/astral-sh/uv:0.5.8@sha256:0bc959d4cc56e42cbd9aa9b63374d84481ee96c32803eea30bd7f16fd99d8d56 /uv /usr/local/bin/uv

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
      build-essential \
      python3-dev \
      python3 \
      libldap2-dev \
      libsasl2-dev \
      libssl-dev \
      ldap-utils\
      slapd \
    && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PYTHON=python3.11
  # UV_PROJECT_ENVIRONMENT=/app

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache \
  uv sync \
    --locked \
    --no-dev \
    --no-install-project

COPY udm_directory_connector udm_directory_connector
RUN --mount=type=cache,target=/root/.cache \
  uv sync --locked --no-dev --no-editable


##########################################################################
FROM build AS test
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
  uv sync

COPY tests tests

# RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
#     && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*
#
#


##########################################################################
FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS final
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

RUN \
groupadd -r app && \
useradd -r -d /app -g app -N app

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
      python3 \
    && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=build --chown=app:app /app /app
COPY --from=build --chown=app:app \
  /usr/lib/x86_64-linux-gnu/libldap-2.5.so.0 \
  /usr/lib/x86_64-linux-gnu/liblber-2.5.so.0 \
  /usr/lib/x86_64-linux-gnu/libsasl2.so.2 \
  /usr/lib/x86_64-linux-gnu/

USER app
WORKDIR /app

CMD [".venv/bin/python3.11", "-m", "udm_directory_connector"]

RUN \
  .venv/bin/python3.11 -V && \
  .venv/bin/python3.11 -m site && \
  .venv/bin/python3.11 -c 'import udm_directory_connector'
