# syntax=docker/dockerfile:1.9
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

# Inspired by: https://hynek.me/articles/docker-uv/

ARG UCS_BASE_IMAGE_TAG=0.18.2-build-2025-06-12
ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-522

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS build
SHELL ["/bin/bash", "-uxo", "pipefail", "-c"]

COPY --from=ghcr.io/astral-sh/uv:0.5.8@sha256:0bc959d4cc56e42cbd9aa9b63374d84481ee96c32803eea30bd7f16fd99d8d56 /uv /usr/local/bin/uv

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
  procps \
  build-essential \
  python3-dev \
  python3 \
  libldap2-dev \
  libsasl2-dev \
  libssl-dev \
  ldap-utils\
  && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

# Download and unpack slapd package since the postinst script
# requires a running LDAP server which "sometimes" fails in Docker
RUN apt-get update && \
  apt-get --assume-yes --verbose-versions --no-install-recommends install slapd; \
  mv /etc/init.d/slapd /etc/init.d/slapd.real \
  && printf '#!/bin/sh\nexit 0\n' > /etc/init.d/slapd \
  && chmod +x /etc/init.d/slapd \
  && dpkg --configure slapd \
  && mv /etc/init.d/slapd.real /etc/init.d/slapd \
  && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PYTHON=python3.11 \
  UV_PROJECT_ENVIRONMENT=/app

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY junkaptor junkaptor
RUN --mount=type=cache,target=/root/.cache \
  uv sync \
  --locked \
  --no-dev \
  --no-install-project

COPY univention univention
RUN --mount=type=cache,target=/root/.cache \
  uv sync --locked --no-dev --no-editable


##########################################################################
FROM build AS test
SHELL ["/bin/bash", "-uxo", "pipefail", "-c"]
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
  uv sync

COPY --from=alpine/helm:3.17.1@sha256:e8d29e13b8218a8cb7b117a10a5210922474a74467bf70b6f3f1f7d9c1818ab0 /usr/bin/helm /usr/local/bin/helm

COPY docker/directory-importer/activate_venv.envsh /entrypoint.d/

##########################################################################
FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS final
SHELL ["/bin/bash", "-uxo", "pipefail", "-c"]

RUN \
  groupadd -r app -g 1000 && \
  useradd -r -d /app -g app -N app -u 1000

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
  python3 \
  libldap-2.5-0 \
  && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=ghcr.io/astral-sh/uv:0.5.8@sha256:0bc959d4cc56e42cbd9aa9b63374d84481ee96c32803eea30bd7f16fd99d8d56 /uv /usr/local/bin/uv

COPY --from=build --chown=app:app /app /app
COPY docker/directory-importer/activate_venv.envsh /entrypoint.d/

USER app
WORKDIR /app

CMD ["directory-importer"]

RUN \
  .venv/bin/python3.11 -V && \
  .venv/bin/python3.11 -m site && \
  .venv/bin/python3.11 -c 'import univention.directory_importer'
