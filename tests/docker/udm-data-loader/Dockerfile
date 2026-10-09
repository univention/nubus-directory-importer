# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

ARG OX_EXTENSION_IMAGE=artifacts.software-univention.de/nubus/images/ox-extension:0.46.0
ARG DATA_LOADER_IMAGE=artifacts.software-univention.de/nubus/images/data-loader:0.107.6

# hadolint ignore=DL3006
FROM ${OX_EXTENSION_IMAGE} AS ox-extension
# hadolint ignore=DL3006
FROM ${DATA_LOADER_IMAGE}

COPY --from=ox-extension /plugins/udm-data-loader/30-ox-connector.yaml /join-data/
