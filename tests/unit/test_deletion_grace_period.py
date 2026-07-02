# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import (
    DEPROVISION_TS_FORMAT,
    Connector,
)
from univention.directory_importer.udm import UDMEntry, UDMModel

PRIMARY_KEY = "6881434e-1bf1-46ea-b20b-94928aa1840b"
DN = "uid=user1,ou=test,dc=example,dc=test"


@pytest.fixture()
def make_connector(connector_yaml_path):
    def _make(grace_days=0):
        config = ConnectorConfig(connector_yaml_path)
        config.udm.deletion_grace_period_days = grace_days
        connector = Connector.__new__(Connector)
        connector._config = config
        connector._udm = mock.Mock()
        return connector

    return _make


def _entry(properties=None):
    return UDMEntry(
        source_primary_key=PRIMARY_KEY,
        dn=DN,
        properties=properties or {},
    )


def test_config_defaults(connector_yaml_path):
    config = ConnectorConfig(connector_yaml_path)
    assert config.udm.deletion_grace_period_days == 0
    assert (
        config.udm.deprovision_timestamp_property
        == "directoryImporterDeprovisionedAt"
    )


def test_delete_without_grace_period(make_connector):
    connector = make_connector(grace_days=0)
    ctr = connector.delete_old_entries(UDMModel.USER, {PRIMARY_KEY: _entry()}, {})
    assert ctr == 1
    connector._udm.delete.assert_called_once_with(UDMModel.USER, DN)
    connector._udm.modify.assert_not_called()


def test_grace_period_deprovisions_first(make_connector):
    connector = make_connector(grace_days=30)
    ctr = connector.delete_old_entries(UDMModel.USER, {PRIMARY_KEY: _entry()}, {})
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    args = connector._udm.modify.call_args
    assert args.args[0] == UDMModel.USER
    assert args.args[1] == DN
    assert args.args[2]["disabled"] is True
    assert "directoryImporterDeprovisionedAt" in args.args[2]


def test_grace_period_not_expired(make_connector):
    connector = make_connector(grace_days=30)
    ts = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        DEPROVISION_TS_FORMAT,
    )
    entry = _entry({"directoryImporterDeprovisionedAt": ts, "disabled": True})
    ctr = connector.delete_old_entries(UDMModel.USER, {PRIMARY_KEY: entry}, {})
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    connector._udm.modify.assert_not_called()


def test_grace_period_expired_deletes(make_connector):
    connector = make_connector(grace_days=30)
    ts = (datetime.now(timezone.utc) - timedelta(days=31)).strftime(
        DEPROVISION_TS_FORMAT,
    )
    entry = _entry({"directoryImporterDeprovisionedAt": ts, "disabled": True})
    ctr = connector.delete_old_entries(UDMModel.USER, {PRIMARY_KEY: entry}, {})
    assert ctr == 1
    connector._udm.delete.assert_called_once_with(UDMModel.USER, DN)


def test_grace_period_does_not_apply_to_groups(make_connector):
    connector = make_connector(grace_days=30)
    ctr = connector.delete_old_entries(UDMModel.GROUP, {PRIMARY_KEY: _entry()}, {})
    assert ctr == 1
    connector._udm.delete.assert_called_once_with(UDMModel.GROUP, DN)
    connector._udm.modify.assert_not_called()


def test_entry_present_in_source_untouched(make_connector):
    connector = make_connector(grace_days=30)
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        {PRIMARY_KEY: _entry()},
        {PRIMARY_KEY: DN},
    )
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    connector._udm.modify.assert_not_called()
