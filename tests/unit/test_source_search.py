# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from unittest.mock import MagicMock, patch

import ldap
import pytest

from univention.directory_importer.__main__ import cli, setup_logging
from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import Connector, ReadSourceDirectoryError

LDAP_RESULT = (
    "result_type_example",
    [[{"dn": "uid=test,ou=people,dc=example,dc=com"}]],
    None,
    [],
)


@pytest.fixture
def udm_mock():
    return MagicMock()


@pytest.fixture
def ldap_mock():
    ldap_mock = MagicMock()
    ldap_mock.whoami_s.return_value = "fake"

    ldap_mock.result3.side_effect = iter(
        [
            LDAP_RESULT,
            LDAP_RESULT,
            LDAP_RESULT,
            ldap.ADMINLIMIT_EXCEEDED,
        ],
    )
    return ldap_mock


@pytest.fixture
def connector(connector_yaml_path, ldap_mock, udm_mock):
    config = ConnectorConfig(connector_yaml_path)
    connector = Connector.__new__(Connector)
    connector._config = config
    connector._ldap_conn = ldap_mock
    connector._udm = udm_mock

    return connector


@pytest.fixture
def test_logging():
    setup_logging("DEBUG")


def test_source_search(connector, test_logging):
    with pytest.raises(ReadSourceDirectoryError):
        dict(
            connector.source_search(
                search_base="foo",
                search_scope=1,
                ldap_filter="foo",
                ldap_attrs="foo",
                range_attrs="foo",
            ),
        )


def test_importer_repeats_after_failed_source_search(
    connector_yaml_path,
    connector,
    udm_mock,
):
    with patch("univention.directory_importer.__main__.Connector") as mock:
        mock.return_value = connector
        cli(
            config_filename=connector_yaml_path,
            log_level="INFO",
            log_conf=None,
            repeat=True,
            repeat_delay=0.001,
            source_password="foo",
            udm_password="bar",
        )


def test_importer_fails_after_failed_source_search(
    connector_yaml_path,
    connector,
    udm_mock,
):
    with patch("univention.directory_importer.__main__.Connector") as mock:
        mock.return_value = connector
        with pytest.raises(SystemExit):
            cli(
                config_filename=connector_yaml_path,
                log_level="INFO",
                log_conf=None,
                repeat=False,
                repeat_delay=0.001,
                source_password="foo",
                udm_password="bar",
            )
