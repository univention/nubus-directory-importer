# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from pathlib import Path

from typer.testing import CliRunner

from univention.directory_importer import __main__
from univention.directory_importer.__main__ import app

runner = CliRunner()


def test_pass_config_filename_as_cli_option(mocker):
    connector_config_mock = mocker.patch.object(__main__, "ConnectorConfig")
    mocker.patch.object(__main__, "Connector")

    runner.invoke(app, ["stub/config.yaml"])

    connector_config_mock.assert_called_once_with(Path("stub/config.yaml"))


def test_reads_config_filename_from_environment(mocker):
    connector_config_mock = mocker.patch.object(__main__, "ConnectorConfig")
    mocker.patch.object(__main__, "Connector")

    runner.invoke(app, [], env={"AD2UCS_CFG": "stub/from-env.yaml"})

    connector_config_mock.assert_called_once_with(Path("stub/from-env.yaml"))
