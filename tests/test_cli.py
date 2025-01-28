# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH


import pytest
from typer.testing import CliRunner

from univention.directory_importer import __main__
from univention.directory_importer.__main__ import app

runner = CliRunner()


@pytest.fixture
def stub_config(tmp_path):
    """Creates a stub configuration file"""
    stub_config = tmp_path / "config.yaml"
    stub_config.write_text("")
    return stub_config


def test_pass_config_filename_as_cli_option(mocker, stub_config):
    connector_config_mock = mocker.patch.object(__main__, "ConnectorConfig")
    mocker.patch.object(__main__, "Connector")

    result = runner.invoke(app, [str(stub_config)])

    assert result.exit_code == 0
    connector_config_mock.assert_called_once_with(stub_config)


def test_reads_config_filename_from_environment(mocker, stub_config):
    connector_config_mock = mocker.patch.object(__main__, "ConnectorConfig")
    mocker.patch.object(__main__, "Connector")

    result = runner.invoke(app, [], env={"AD2UCS_CFG": str(stub_config)})

    assert result.exit_code == 0
    connector_config_mock.assert_called_once_with(stub_config)


def test_fails_if_config_path_is_a_directory(mocker, tmp_path):
    result = runner.invoke(app, str(tmp_path))
    assert result.exit_code != 0


def test_fails_if_config_file_does_not_exist(mocker, tmp_path):
    missing_file = tmp_path / "does-not-exist.yaml"
    result = runner.invoke(app, str(missing_file))
    assert result.exit_code != 0
