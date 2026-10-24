# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
import yaml

from univention.testing.helm.base import Base
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


class TestConfigFileDeletionSafeguard(Base):
    """
    the rendered config file of the deletion safeguard, read with the config
    loader of the importer if available
    """

    template_file = "templates/configmap-config-file.yaml"

    def render(self, helm, chart_path, values, tmp_path):
        configmap = self.helm_template_file(
            helm,
            chart_path,
            values,
            self.template_file,
        )
        content = configmap["data"]["config.yaml"]
        rendered = yaml.safe_load(content)["udm"]
        try:
            from univention.directory_importer.config import ConnectorConfig
        except ImportError:
            # the helm test container does not contain the importer
            return rendered, None
        path = tmp_path / "config.yaml"
        path.write_text(content)
        return rendered, ConnectorConfig(path, source_password="x", udm_password="x")

    def test_defaults(self, helm, chart_path, tmp_path):
        rendered, config = self.render(helm, chart_path, {}, tmp_path)
        assert rendered["max_deletion_ratio"] == 0.1
        assert rendered.get("max_deletions") is None
        if config:
            assert config.udm.max_deletion_ratio == 0.1
            assert config.udm.max_deletions is None

    def test_limits(self, helm, chart_path, tmp_path):
        values = {
            "configFile": {
                "udm": {"max_deletion_ratio": 0.01, "max_deletions": 50},
            },
        }
        rendered, config = self.render(helm, chart_path, values, tmp_path)
        assert rendered["max_deletion_ratio"] == 0.01
        assert rendered["max_deletions"] == 50
        if config:
            assert config.udm.max_deletion_ratio == 0.01
            assert config.udm.max_deletions == 50

    def test_ratio_disabled(self, helm, chart_path, tmp_path):
        values = {"configFile": {"udm": {"max_deletion_ratio": 1.0}}}
        rendered, config = self.render(helm, chart_path, values, tmp_path)
        assert rendered["max_deletion_ratio"] == 1.0
        if config:
            assert config.udm.max_deletion_ratio == 1.0

    def test_ratio_null_not_supported(self, helm, chart_path, tmp_path):
        """
        Helm removes keys set to null from the default values, so null does
        not disable the check, use 1.0 instead
        """
        values = {"configFile": {"udm": {"max_deletion_ratio": None}}}
        rendered, config = self.render(helm, chart_path, values, tmp_path)
        assert "max_deletion_ratio" not in rendered
        if config:
            assert config.udm.max_deletion_ratio == 0.1
