# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import (
    DEPROVISION_TS_FORMAT,
    Connector,
    DeletionsBlockedError,
)
from univention.directory_importer.udm import UDMEntry, UDMModel

TS_PROPERTY = "directoryImporterDeprovisionedAt"


@pytest.fixture()
def make_connector(connector_yaml_path):
    def _make(ratio=0.1, max_deletions=None, force=False, grace_days=0):
        config = ConnectorConfig(connector_yaml_path)
        config.udm.max_deletion_ratio = ratio
        config.udm.max_deletions = max_deletions
        config.udm.deletion_grace_period_days = grace_days
        connector = Connector.__new__(Connector)
        connector._config = config
        connector._udm = mock.Mock()
        connector._force_deletions = force
        connector._deletions_blocked = []
        return connector

    return _make


def _entries(count, properties=None, prefix="key"):
    return {
        f"{prefix}-{i}": UDMEntry(
            source_primary_key=f"{prefix}-{i}",
            dn=f"uid={prefix}{i},ou=test,dc=example,dc=test",
            properties=dict(properties or {}),
        )
        for i in range(count)
    }


def _keep(entries, count):
    """primary keys of the first `count` entries, as if still in source"""
    return set(list(entries)[:count])


def _ts(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime(
        DEPROVISION_TS_FORMAT,
    )


@pytest.mark.parametrize(
    "existing,ratio,max_deletions,expected",
    [
        (100, 0.1, None, 10),
        (30, 0.1, None, 3),
        # rounded down, the ratio is never exceeded
        (29, 0.1, None, 2),
        (5, 0.1, None, 0),
        (1, 0.1, None, 0),
        # 0.7 * 10 = 6.999999999999999
        (10, 0.7, None, 7),
        (35000, 0.01, None, 350),
        (35000, 0.1, 50, 50),
        (100, 0.1, 50, 10),
        (100, None, 5, 5),
        (100, None, None, None),
        (100, 1.0, None, 100),
        (100, 0.0, None, 0),
    ],
)
def test_deletion_limit(make_connector, existing, ratio, max_deletions, expected):
    connector = make_connector(ratio=ratio, max_deletions=max_deletions)
    assert connector._deletion_limit(existing) == expected


def test_deletions_within_limit(make_connector):
    connector = make_connector()
    entries = _entries(100)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, _keep(entries, 90))
    assert ctr == 10
    assert connector._udm.delete.call_count == 10
    assert connector._deletions_blocked == []


def test_deletions_exceeding_ratio_blocked(make_connector):
    connector = make_connector()
    entries = _entries(100)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, _keep(entries, 89))
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.USER]


def test_small_directory_blocked(make_connector):
    """one of five entries is 20 %, more than the default of 10 %"""
    connector = make_connector()
    entries = _entries(5)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, _keep(entries, 4))
    assert ctr == 0
    connector._udm.delete.assert_not_called()


def test_empty_source_blocked(make_connector):
    connector = make_connector()
    entries = _entries(35)
    ctr = connector.delete_old_entries(UDMModel.GROUP, entries, set())
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.GROUP]


def test_deletions_exceeding_max_deletions_blocked(make_connector):
    connector = make_connector(max_deletions=3)
    entries = _entries(100)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, _keep(entries, 96))
    assert ctr == 0
    connector._udm.delete.assert_not_called()


@pytest.mark.parametrize("ratio", [None, 1.0])
def test_safeguard_disabled(make_connector, ratio):
    connector = make_connector(ratio=ratio, max_deletions=None)
    entries = _entries(10)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, set())
    assert ctr == 10


def test_force_deletions(make_connector):
    connector = make_connector(force=True)
    entries = _entries(10)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, set())
    assert ctr == 10
    assert connector._deletions_blocked == []


def test_transform_errors_block_deletions(make_connector):
    connector = make_connector()
    entries = _entries(100)
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        entries,
        _keep(entries, 99),
        transform_error_count=1,
    )
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.USER]


def test_transform_errors_without_obsolete_entries(make_connector):
    connector = make_connector()
    entries = _entries(10)
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        entries,
        set(entries),
        transform_error_count=1,
    )
    assert ctr == 0
    assert connector._deletions_blocked == []


def test_transform_errors_forced(make_connector):
    connector = make_connector(force=True)
    entries = _entries(100)
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        entries,
        _keep(entries, 99),
        transform_error_count=1,
    )
    assert ctr == 1


def test_grace_period_deprovisioning_blocked(make_connector):
    connector = make_connector(grace_days=30)
    entries = _entries(100)
    ctr = connector.delete_old_entries(UDMModel.USER, entries, set())
    assert ctr == 0
    connector._udm.modify.assert_not_called()
    connector._udm.delete.assert_not_called()


def test_grace_period_waiting_entries_not_counted(make_connector):
    """entries already deprovisioned do not count against the limit"""
    connector = make_connector(grace_days=30)
    active = _entries(50)
    waiting = _entries(50, {TS_PROPERTY: _ts(1), "disabled": True}, prefix="old")
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        active | waiting,
        _keep(active, 45),
    )
    assert ctr == 0
    assert connector._udm.modify.call_count == 5
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == []


def test_grace_period_expired_deletions_not_counted(make_connector):
    """
    only the deprovisioning counts against the limit, not the deletion after
    the grace period: 10 new and 10 expired entries of 100 do not exceed 10 %
    """
    connector = make_connector(grace_days=30)
    active = _entries(90)
    expired = _entries(10, {TS_PROPERTY: _ts(31), "disabled": True}, prefix="old")
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        active | expired,
        _keep(active, 80),
    )
    assert ctr == 10
    assert connector._udm.delete.call_count == 10
    assert connector._udm.modify.call_count == 10
    assert connector._deletions_blocked == []


def test_grace_period_expired_deletions_blocked_by_transform_errors(make_connector):
    connector = make_connector(grace_days=30)
    active = _entries(90)
    expired = _entries(1, {TS_PROPERTY: _ts(31), "disabled": True}, prefix="old")
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        active | expired,
        set(active),
        transform_error_count=1,
    )
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.USER]


def test_grace_period_invalid_timestamp_blocks_deletions(make_connector):
    connector = make_connector(grace_days=30)
    active = _entries(90)
    invalid = _entries(1, {TS_PROPERTY: "yesterday", "disabled": True}, prefix="bad")
    expired = _entries(1, {TS_PROPERTY: _ts(31), "disabled": True}, prefix="old")
    ctr = connector.delete_old_entries(
        UDMModel.USER,
        active | invalid | expired,
        set(active),
    )
    assert ctr == 0
    connector._udm.delete.assert_not_called()
    connector._udm.modify.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.USER]


def _prep_properties(model, attrs):
    """simplified UDMClient.prep_properties: single values as str"""
    res = {}
    for key, vals in attrs.items():
        vals = [v.decode() if isinstance(v, bytes) else v for v in vals]
        res[key] = vals[0] if len(vals) == 1 and key != "users" else vals
    return res


@pytest.fixture()
def udm_connector(make_connector):
    """connector with the real transformation and a mocked UDM"""

    def _make(**kwargs):
        connector = make_connector(**kwargs)
        connector._udm.prep_properties.side_effect = _prep_properties
        connector._udm.base_position = "dc=example,dc=test"
        props = connector._config.udm.user_properties
        props |= connector._config.udm.group_properties
        connector._udm.get_template.return_value = {
            "properties": {prop: None for prop in props},
        }
        return connector

    return _make


def test_sync_entries_add_and_modify_despite_blocked_deletions(udm_connector):
    connector = udm_connector()
    entries = _entries(10)
    source = {
        entry.dn: {"key": [key], "name": [key]}
        for key, entry in list(entries.items())[:8]
    }
    # one modified and one new entry
    source[entries["key-0"].dn]["name"] = ["changed"]
    source["uid=new,ou=test,dc=example,dc=test"] = {"key": ["new"], "name": ["new"]}
    _, error_count, delete_count, _ = connector.sync_entries(
        model=UDMModel.GROUP,
        position="ou=test,dc=example,dc=test",
        source=source,
        primary_key="key",
        properties={"name"},
        trans=lambda entry: entry,
        old_entries={
            key: UDMEntry(entry.source_primary_key, entry.dn, {"name": key})
            for key, entry in entries.items()
        },
    )
    assert error_count == 0
    assert delete_count == 0
    connector._udm.delete.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.GROUP]
    connector._udm.modify.assert_called_once()
    assert connector._udm.modify.call_args.args[2] == {"name": "changed"}
    connector._udm.add.assert_called_once()
    assert connector._udm.add.call_args.args[1]["name"] == "new"


def test_sync_entries_transform_error_keeps_target_entry(udm_connector):
    """
    a source entry which cannot be transformed must not lead to the removal
    of its target entry
    """
    connector = udm_connector()
    entries = _entries(20)
    source = {
        entry.dn: {"key": [key], "name": [key]} for key, entry in entries.items()
    }
    # e.g. the primary key attribute is not readable
    del source[entries["key-0"].dn]["key"]
    _, error_count, delete_count, _ = connector.sync_entries(
        model=UDMModel.USER,
        position="ou=test,dc=example,dc=test",
        source=source,
        primary_key="key",
        properties={"name"},
        trans=lambda entry: entry,
        old_entries={
            key: UDMEntry(entry.source_primary_key, entry.dn, {"name": key})
            for key, entry in entries.items()
        },
    )
    assert error_count == 1
    assert delete_count == 0
    connector._udm.delete.assert_not_called()
    connector._udm.modify.assert_not_called()
    assert connector._deletions_blocked == [UDMModel.USER]


USER_UUID = "6881434e-1bf1-46ea-b20b-94928aa1840b"
GROUP_UUID = "0b9a7c42-8b1e-4d6c-9f4a-2c6f1a3e5d7b"
USER_SOURCE_DN = "uid=user1,o=source"
USER_TARGET_DN = "uid=user1,ou=users,dc=example,dc=test"
GROUP_TARGET_DN = "cn=group1,ou=groups,dc=example,dc=test"


@pytest.fixture()
def membership(mocker):
    """
    a user in a group, the entryUUID of the user is not readable in the
    source directory, e.g. because of an ACL
    """
    source_users = [
        (
            USER_SOURCE_DN,
            {"uid": [b"user1"], "givenName": [b"User"], "sn": [b"One"]},
        ),
    ]
    source_groups = [
        (
            "cn=group1,o=source",
            {
                "entryUUID": [GROUP_UUID.encode()],
                "cn": [b"group1"],
                "member": [USER_SOURCE_DN.encode()],
            },
        ),
    ]
    old_users = {
        USER_UUID: UDMEntry(
            USER_UUID,
            USER_TARGET_DN,
            {"univentionObjectIdentifier": USER_UUID, "username": "user1"},
        ),
    }
    old_groups = {
        GROUP_UUID: UDMEntry(
            GROUP_UUID,
            GROUP_TARGET_DN,
            {
                "univentionObjectIdentifier": GROUP_UUID,
                "name": "group1",
                "users": [USER_TARGET_DN],
                "nestedGroup": [],
            },
        ),
    }
    mocker.patch.object(
        Connector,
        "_get_existing_udm_objects",
        return_value=(old_users, old_groups),
    )
    mocker.patch.object(Connector, "log_summary")
    search = mocker.patch.object(
        Connector,
        "source_search",
        side_effect=[source_users, source_groups],
    )
    return {
        "search": search,
        "source_users": source_users,
        "source_groups": source_groups,
        "old_users": old_users,
        "old_groups": old_groups,
    }


def _group_modifications(connector):
    return [
        call.args[2]
        for call in connector._udm.modify.call_args_list
        if call.args[0] == UDMModel.GROUP
    ]


def test_membership_lost_by_group_sync(udm_connector, membership):
    """
    the group sync alone removes a user it cannot map from the group,
    which is why it is skipped if the removal of users is blocked
    """
    connector = udm_connector()
    membership["search"].side_effect = [membership["source_groups"]]
    connector._sync_groups(
        dict(membership["source_users"]),
        {key: entry.dn for key, entry in membership["old_users"].items()},
        membership["old_groups"],
    )
    assert _group_modifications(connector) == [{"users": []}]


def test_membership_kept_if_user_removal_blocked(udm_connector, membership):
    # only the transformation error blocks the removal, not the limit
    connector = udm_connector(ratio=None)
    with pytest.raises(DeletionsBlockedError):
        connector()
    connector._udm.delete.assert_not_called()
    assert _group_modifications(connector) == []
    assert connector._deletions_blocked == [UDMModel.USER]


def test_membership_sync_forced(udm_connector, membership):
    """with --force-deletions the user is removed and the group is synced"""
    connector = udm_connector(force=True)
    connector()
    connector._udm.delete.assert_called_once_with(UDMModel.USER, USER_TARGET_DN)
    assert _group_modifications(connector) == [{"users": []}]


@pytest.fixture()
def run_connector(make_connector, mocker):
    """
    connector with mocked source and sync, `blocked` simulates blocked
    removals of users
    """

    def _run(blocked=False):
        connector = make_connector()
        connector._udm.base_position = "dc=example,dc=test"
        # Connector uses __slots__, so patch the methods on the class
        patch = mocker.patch.object
        patch(Connector, "_get_existing_udm_objects", return_value=({}, {}))
        patch(Connector, "source_search", return_value=[])
        patch(Connector, "log_summary")
        patch(Connector, "_sync_groups", return_value=(0, 0, 0))

        def sync_entries(model, *args, **kwargs):
            if model == UDMModel.USER and blocked:
                connector._deletions_blocked.append(UDMModel.USER)
            return 0, 0, 0, {}

        patch(Connector, "sync_entries", side_effect=sync_entries)
        return connector

    return _run


def test_groups_synced(run_connector):
    connector = run_connector()
    assert connector() == (0, 0, 0)
    connector._sync_groups.assert_called_once()


def test_groups_skipped_if_user_removal_blocked(run_connector):
    connector = run_connector(blocked=True)
    with pytest.raises(DeletionsBlockedError):
        connector()
    connector._sync_groups.assert_not_called()


def test_blocked_state_reset_for_each_run(run_connector):
    connector = run_connector(blocked=True)
    with pytest.raises(DeletionsBlockedError):
        connector()
    connector.sync_entries.side_effect = lambda *args, **kwargs: (0, 0, 0, {})
    assert connector() == (0, 0, 0)
    connector._sync_groups.assert_called_once()
