# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from unittest.mock import MagicMock

import ldap
import pytest

from univention.directory_importer.__main__ import setup_logging
from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import Connector


def test_source_search(connector_yaml_path):
    fake_ldap_conn = MagicMock()
    fake_ldap_conn.whoami_s.return_value = "fake"

    ldap_result = (
        "result_type_example",
        [[{"dn": "uid=test,ou=people,dc=example,dc=com"}]],
        None,
        [],
    )
    fake_ldap_conn.result3.side_effect = iter(
        [
            ldap_result,
            ldap_result,
            ldap_result,
            ldap.ADMINLIMIT_EXCEEDED,
        ],
    )

    setup_logging("DEBUG")
    config = ConnectorConfig(connector_yaml_path)
    connector = Connector.__new__(Connector)
    connector._config = config

    connector._ldap_conn = fake_ldap_conn

    with pytest.raises(ldap.ADMINLIMIT_EXCEEDED):
        dict(
            connector.source_search(
                search_base=config.src.user_base,
                search_scope=config.src.user_scope,
                ldap_filter=config.src.user_filter,
                ldap_attrs=config.src.user_attrs,
                range_attrs=config.src.user_range_attrs,
            ),
        )
