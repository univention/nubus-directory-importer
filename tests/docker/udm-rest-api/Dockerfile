# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

ARG UDM_REST_API_IMAGE=artifacts.software-univention.de/nubus/images/udm-rest-api:0.46.7
ARG OX_EXTENSION_IMAGE=artifacts.software-univention.de/nubus/images/ox-extension:0.46.0

# hadolint ignore=DL3006
FROM ${OX_EXTENSION_IMAGE} AS ox-extension
# hadolint ignore=DL3006
FROM ${UDM_REST_API_IMAGE}

COPY --from=ox-extension /plugins/udm-handlers/oxmail \
    /usr/lib/python3/dist-packages/univention/admin/handlers/oxmail
COPY --from=ox-extension /plugins/udm-handlers/oxresources \
    /usr/lib/python3/dist-packages/univention/admin/handlers/oxresources
COPY --from=ox-extension /plugins/udm-hooks.d/ \
    /usr/lib/python3/dist-packages/univention/admin/hooks.d/
COPY --from=ox-extension /plugins/udm-syntax.d/ \
    /usr/lib/python3/dist-packages/univention/admin/syntax.d/
