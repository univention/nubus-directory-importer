# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
from pytest_helm.manifests.configmap import (
    ConfigMap,
    OptionalEnvVariables,
    RequiredEnvVariables,
)


class TestConfigMap(ConfigMap):
    manifest = "templates/configmap.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.logLevel", "LOG_LEVEL"),
        ("config.repeat", "REPEAT"),
        ("config.repeatDelay", "REPEAT_DELAY"),
    ],
)
class TestRequiredConfigMapEnv(RequiredEnvVariables):
    manifest = "templates/configmap.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.loggingConfig", "LOG_CONF"),
    ],
)
class TestOptionalConfigMapEnv(OptionalEnvVariables):
    manifest = "templates/configmap.yaml"


class TestConfigMapConfigFile(ConfigMap):
    manifest = "templates/configmap-config-file.yaml"
