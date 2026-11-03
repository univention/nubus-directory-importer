# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
import strictyaml

from univention.directory_importer.config import ConnectorConfig

UDM_PASSWORD = "udm_password"
SOURCE_PASSWORD = "source_password"


@pytest.fixture
def connector_yaml(connector_yaml_path):
    with open(connector_yaml_path, "r") as f:
        return strictyaml.load(f.read())


def test_source_config_password_override(connector_yaml_path):
    """Test that SourceConfig takes password from argument if set"""
    config = ConnectorConfig(connector_yaml_path, source_password=SOURCE_PASSWORD)
    assert config.src.password == SOURCE_PASSWORD.encode("utf-8")


def test_source_config_password_from_yaml(connector_yaml_path, connector_yaml):
    """Test that SourceConfig takes password from YAML if argument is not set"""
    config = ConnectorConfig(connector_yaml_path)
    assert config.src.password == connector_yaml["source"]["password"].value.encode(
        "utf-8",
    )


def test_udm_config_password_override(connector_yaml_path):
    """Test that UDMConfig takes password from environment variable if set"""
    config = ConnectorConfig(connector_yaml_path, udm_password=UDM_PASSWORD)
    assert config.udm.password == UDM_PASSWORD


def test_udm_config_password_from_yaml(connector_yaml_path, connector_yaml):
    """Test that UDMConfig takes password from YAML if env variable is not set"""
    config = ConnectorConfig(connector_yaml_path)
    assert config.udm.password == connector_yaml["udm"]["password"].text


@pytest.fixture
def write_udm_config(tmp_path, connector_yaml_path):
    """writes the test config with additional lines in the udm section"""

    def _write(*udm_lines):
        with open(connector_yaml_path, "r") as f:
            content = f.read()
        extra = "".join(f"    {line}\n" for line in udm_lines)
        content = content.replace("udm:\n", f"udm:\n{extra}", 1)
        path = tmp_path / "connector.yml"
        path.write_text(content)
        return path

    return _write


def test_udm_config_deletion_safeguard_defaults(connector_yaml_path):
    config = ConnectorConfig(connector_yaml_path)
    assert config.udm.max_deletion_ratio == 0.1
    assert config.udm.max_deletions == 100


def test_udm_config_deletion_safeguard(write_udm_config):
    config = ConnectorConfig(
        write_udm_config("max_deletion_ratio: 0.01", "max_deletions: 50"),
    )
    assert config.udm.max_deletion_ratio == 0.01
    assert config.udm.max_deletions == 50


def test_udm_config_deletion_safeguard_disabled(write_udm_config):
    config = ConnectorConfig(
        write_udm_config("max_deletion_ratio: null", "max_deletions: null"),
    )
    assert config.udm.max_deletion_ratio is None
    assert config.udm.max_deletions is None


@pytest.mark.parametrize(
    "line",
    ["max_deletion_ratio: 1.5", "max_deletion_ratio: -0.1", "max_deletions: -1"],
)
def test_udm_config_deletion_safeguard_invalid(write_udm_config, line):
    config = write_udm_config(line)
    with pytest.raises(ValueError):
        ConnectorConfig(config)
