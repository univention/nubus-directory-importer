# syntax=docker/dockerfile:1.29@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

# Inspired by: https://hynek.me/articles/docker-uv/

ARG UCS_BASE_IMAGE=gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python
ARG UCS_BASE_IMAGE_TAG=5.3.0-build.20261119@sha256:f5810786b9a4ed68f05cd8ecbd6fe547d241717ae855cf397ac57587603a2ab1

FROM ${UCS_BASE_IMAGE}:${UCS_BASE_IMAGE_TAG} AS build
SHELL ["/bin/bash", "-uxo", "pipefail", "-c"]

COPY --from=ghcr.io/astral-sh/uv:0.13.8@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85 /uv /usr/local/bin/uv

RUN apt-get --assume-yes --verbose-versions --no-install-recommends install \
  build-essential \
  python3-dev \
  libldap2-dev \
  libsasl2-dev \
  libssl-dev \
  ldap-utils\
  slapd \
  && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PYTHON=python3.13
# UV_PROJECT_ENVIRONMENT=/app

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
  libldap2 \
  && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=ghcr.io/astral-sh/uv:0.13.8@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85 /uv /usr/local/bin/uv

COPY --from=build --chown=app:app /app /app
COPY docker/directory-importer/activate_venv.envsh /entrypoint.d/

USER app
WORKDIR /app

CMD ["directory-importer"]

RUN \
  .venv/bin/python3.13 -V && \
  .venv/bin/python3.13 -m site && \
  .venv/bin/python3.13 -c 'import univention.directory_importer'
