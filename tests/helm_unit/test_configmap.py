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

    def test_metrics_disabled_by_default(self, helm, chart_path):
        configmap = self.helm_template_file(helm, chart_path, {}, self.template_file)
        assert "METRICS_PORT" not in configmap["data"]
        assert "METRICS_BIND_ADDRESS" not in configmap["data"]

    def test_metrics_port(self, helm, chart_path):
        values = {"metrics": {"enabled": True, "port": 9999}}
        configmap = self.helm_template_file(helm, chart_path, values, self.template_file)
        assert configmap["data"]["METRICS_PORT"] == "9999"
        assert "METRICS_BIND_ADDRESS" not in configmap["data"]


@pytest.mark.parametrize(
    "key, env_var",
    [
        ("config.logLevel", "LOG_LEVEL"),
        ("config.repeat", "REPEAT"),
        ("config.repeatDelay", "REPEAT_DELAY"),
        ("config.forceDeletions", "FORCE_DELETIONS"),
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


@pytest.mark.parametrize("key, env_var", [("metrics.bindAddress", "METRICS_BIND_ADDRESS")])
class TestMetricsBindAddress(OptionalEnvVariables):
    template_file = "templates/configmap.yaml"

    def helm_template_file(self, helm, chart, values, template_file, helm_args=None):
        values["metrics"]["enabled"] = True
        return super().helm_template_file(helm, chart, values, template_file, helm_args)


class TestConfigMapConfigFile(ConfigMap):
    template_file = "templates/configmap-config-file.yaml"
