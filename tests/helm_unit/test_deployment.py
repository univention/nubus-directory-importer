# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH


import pytest
from pytest_helm.manifests.container import Container
from pytest_helm.manifests.deployment import Deployment


class TestDeployment(Deployment):
    manifest = "templates/deployment.yaml"

    def values(self, localpart: dict) -> dict:
        return localpart


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("udm", "UDM_PASSWORD"),
        ("sourceDirectory", "SOURCE_PASSWORD"),
    ],
)
class TestMainContainer(Container):
    manifest = "templates/deployment.yaml"
    name = "directory-importer"
