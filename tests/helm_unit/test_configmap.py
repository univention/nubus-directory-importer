# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest

from univention.testing.helm.configmap import (
    ConfigMap,
    OptionalEnvVariables,
    RequiredEnvVariables,
)


class TestConfigMap(ConfigMap):
    template_file = "templates/configmap.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.logLevel", "LOG_LEVEL"),
        ("config.repeat", "REPEAT"),
        ("config.repeatDelay", "REPEAT_DELAY"),
    ],
)
class TestRequiredConfigMapEnv(RequiredEnvVariables):
    template_file = "templates/configmap.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.loggingConfig", "LOG_CONF"),
    ],
)
class TestOptionalConfigMapEnv(OptionalEnvVariables):
    template_file = "templates/configmap.yaml"


class TestConfigMapConfigFile(ConfigMap):
    template_file = "templates/configmap-config-file.yaml"
