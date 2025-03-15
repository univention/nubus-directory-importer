# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH


import pytest

from univention.testing.helm.container import ContainerEnvVarSecret
from univention.testing.helm.deployment import Deployment


class TestDeployment(Deployment):
    template_file = "templates/deployment.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("udm", "UDM_PASSWORD"),
        ("sourceDirectory", "SOURCE_PASSWORD"),
    ],
)
class TestMainContainer(ContainerEnvVarSecret):
    template_file = "templates/deployment.yaml"
    container_name = "directory-importer"
