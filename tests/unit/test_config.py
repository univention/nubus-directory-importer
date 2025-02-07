# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
import strictyaml

from univention.directory_importer.config import ConnectorConfig

UDM_PASSWORD = "udm_password"
SOURCE_PASSWORD = "source_password"


@pytest.fixture()
def connector_yaml_path():
    return "tests/data/connector.yml"


@pytest.fixture()
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
