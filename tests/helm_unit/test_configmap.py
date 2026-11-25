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


class EnableMetricsForEnvTests:
    def helm_template_file(self, helm, chart, values, template_file, helm_args=None):
        if "metrics" in values:
            values["metrics"]["enabled"] = True
        return super().helm_template_file(helm, chart, values, template_file, helm_args)


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.logLevel", "LOG_LEVEL"),
        ("config.repeat", "REPEAT"),
        ("config.repeatDelay", "REPEAT_DELAY"),
        ("config.forceDeletions", "FORCE_DELETIONS"),
        ("metrics.port", "METRICS_PORT"),
    ],
)
class TestRequiredConfigMapEnv(EnableMetricsForEnvTests, RequiredEnvVariables):
    template_file = "templates/configmap.yaml"


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.loggingConfig", "LOG_CONF"),
        ("metrics.bindAddress", "METRICS_BIND_ADDRESS"),
    ],
)
class TestOptionalConfigMapEnv(EnableMetricsForEnvTests, OptionalEnvVariables):
    template_file = "templates/configmap.yaml"


class TestConfigMapConfigFile(ConfigMap):
    template_file = "templates/configmap-config-file.yaml"
