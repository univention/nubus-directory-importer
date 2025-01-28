# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH


import os
from unittest import mock

import pytest
from typer.testing import CliRunner

from univention.directory_importer import __main__
from univention.directory_importer.__main__ import app

runner = CliRunner()


class StopException(Exception):
    """Utility to force stop the repeated iteration."""


@pytest.fixture(autouse=True)
def mock_connector(mocker):
    """Replace the Connector object with a Mock."""
    return mocker.patch.object(__main__, "Connector")


@pytest.fixture(autouse=True)
def super_short_default_delay(mocker):
    value = 0.001
    mocker.patch.object(__main__.Repeater, "DEFAULT_DELAY", value)
    return value


@pytest.fixture
def mock_connector_config(mocker):
    return mocker.patch.object(__main__, "ConnectorConfig")


@pytest.fixture
def stub_config(tmp_path):
    """Creates a stub configuration file."""
    stub_config = tmp_path / "config.yaml"
    stub_config.write_text("")
    return stub_config


@pytest.fixture
def stub_log_conf(tmp_path):
    """Created a stub log configuration file."""
    stub_log_conf = tmp_path / "log-conf.yaml"
    stub_log_conf.write_text("")
    return stub_log_conf


def test_pass_config_filename_as_cli_option(mock_connector_config, stub_config):
    result = runner.invoke(app, [str(stub_config)])
    assert result.exit_code == 0
    mock_connector_config.assert_called_once_with(stub_config)


def test_reads_config_filename_from_environment(mock_connector_config, stub_config):
    result = runner.invoke(app, [], env={"CONFIG_FILENAME": str(stub_config)})
    assert result.exit_code == 0
    mock_connector_config.assert_called_once_with(stub_config)


def test_fails_if_config_path_is_a_directory(tmp_path):
    result = runner.invoke(app, str(tmp_path))
    assert result.exit_code != 0


def test_fails_if_config_file_does_not_exist(tmp_path):
    missing_file = tmp_path / "does-not-exist.yaml"
    result = runner.invoke(app, str(missing_file))
    assert result.exit_code != 0


def test_set_log_level_via_cli(mocker):
    mocker.patch.dict("os.environ")
    os.environ.pop("LOG_LEVEL", None)
    setup_logging_mock = mocker.patch.object(__main__, "setup_logging")

    result = runner.invoke(app, ["--log-level", "debug"])

    assert result.exit_code == 0
    setup_logging_mock.assert_called_once_with("DEBUG")


def test_set_log_level_via_environment(mocker):
    mocker.patch.dict("os.environ", {"LOG_LEVEL": "debug"})
    setup_logging_mock = mocker.patch.object(__main__, "setup_logging")

    result = runner.invoke(app, ["--log-level", "debug"])

    assert result.exit_code == 0
    setup_logging_mock.assert_called_once_with("DEBUG")


def test_logs_by_default_on_level_info(mocker):
    mocker.patch.dict("os.environ")
    os.environ.pop("LOG_LEVEL", None)
    setup_logging_mock = mocker.patch.object(__main__, "setup_logging")

    result = runner.invoke(app)

    assert result.exit_code == 0
    setup_logging_mock.assert_called_once_with("INFO")


def test_set_log_conf_via_cli(mocker, stub_log_conf):
    mocker.patch.dict("os.environ")
    os.environ.pop("LOG_CONF", None)
    file_config_mock = mocker.patch("logging.config.fileConfig")

    result = runner.invoke(app, ["--log-conf", str(stub_log_conf)])

    assert result.exit_code == 0
    file_config_mock.assert_called_once_with(stub_log_conf)


def test_set_log_conf_via_environment(mocker, stub_log_conf):
    mocker.patch.dict("os.environ")
    os.environ["LOG_CONF"] = str(stub_log_conf)
    file_config_mock = mocker.patch("logging.config.fileConfig")

    result = runner.invoke(app)

    assert result.exit_code == 0
    file_config_mock.assert_called_once_with(stub_log_conf)


def test_log_conf_overrides_log_level(mocker, stub_log_conf):
    mocker.patch.dict("os.environ")
    os.environ |= {
        "LOG_CONF": str(stub_log_conf),
        "LOG_LEVEL": "debug",
    }
    file_config_mock = mocker.patch("logging.config.fileConfig")
    setup_logging_mock = mocker.patch.object(__main__, "setup_logging")

    result = runner.invoke(app)

    assert result.exit_code == 0
    file_config_mock.assert_called_once_with(stub_log_conf)
    setup_logging_mock.assert_not_called()


def test_calls_connector_by_default_only_once(mock_connector):
    result = runner.invoke(app)
    assert result.exit_code == 0
    mock_connector().assert_called_once()


def test_calls_connector_repeatedly(mock_connector, mocker):
    mock_connector_instance = mock_connector()
    mock_connector_instance.side_effect = [None, StopException("STOP")]

    with pytest.raises(StopException):
        runner.invoke(
            app,
            ["--repeat", "--repeat-delay", "0.002"],
            catch_exceptions=False,
        )

    assert mock_connector_instance.call_count == 2


@pytest.mark.parametrize("repeat_value", ["1", "yes", "true"])
def test_calls_connector_repeatedly_env(repeat_value, mock_connector, mocker):
    mock_connector_instance = mock_connector()
    mock_connector_instance.side_effect = [None, StopException("STOP")]
    mocker.patch.dict("os.environ")
    os.environ |= {
        "REPEAT": repeat_value,
    }

    with pytest.raises(StopException):
        runner.invoke(app, catch_exceptions=False)

    assert mock_connector_instance.call_count == 2


def test_repeat_with_custom_delay(mocker):
    repeater_mock = mocker.patch.object(__main__, "Repeater")
    result = runner.invoke(
        app,
        ["--repeat", "--repeat-delay", "10"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    repeater_mock.assert_called_once_with(target=mock.ANY, delay=10)


def test_repeat_with_custom_delay_env(mocker):
    mocker.patch.dict("os.environ")
    os.environ |= {
        "REPEAT": "1",
        "REPEAT_DELAY": "10",
    }
    repeater_mock = mocker.patch.object(__main__, "Repeater")

    result = runner.invoke(app, catch_exceptions=False)

    assert result.exit_code == 0
    repeater_mock.assert_called_once_with(target=mock.ANY, delay=10)
