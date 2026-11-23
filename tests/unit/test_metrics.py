# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

import logging
import socket
import urllib.request
from collections import defaultdict
from unittest import mock

import pytest
from prometheus_client import REGISTRY

from univention.directory_importer import metrics
from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import Connector, ReadSourceDirectoryError
from univention.directory_importer.udm import UDMClient, UDMEntry, UDMMethod, UDMModel

USERS = UDMModel.USER.value
GROUPS = UDMModel.GROUP.value


def sample(name, **labels):
    return REGISTRY.get_sample_value(name, labels)


def model_samples(model):
    return (
        sample("nubus_directory_importer_last_run_source_entries", model=model),
        sample("nubus_directory_importer_last_run_errors", model=model),
        sample("nubus_directory_importer_last_run_deleted_entries", model=model),
    )


def source_entries(prefix, count):
    return [
        (f"cn={prefix}{i},o=source", {"entryUUID": [f"{prefix}{i}".encode()]})
        for i in range(count)
    ]


def old_entries(prefix, count):
    return {
        f"{prefix}-old{i}": UDMEntry(
            source_primary_key=f"{prefix}-old{i}",
            dn=f"cn={prefix}-old{i},dc=example,dc=test",
            properties={},
        )
        for i in range(count)
    }


class FakeSource:
    """
    Stand-in for the source directory and the UDM REST API of a connector.
    Entries listed in `failing` make the UDM add request fail.
    """

    def __init__(self, connector, mocker):
        self.users = []
        self.groups = []
        self.old_users = {}
        self.old_groups = {}
        self.failing = set()
        self.group_search_error = None
        self.on_group_search = None
        connector._udm.base_position = "dc=example,dc=test"
        connector._udm._req_count = UDMClient._init_counter(0)
        connector._udm._status_count = UDMClient._init_counter(defaultdict)
        connector._udm.list.side_effect = self._list
        connector._udm.prep_properties.side_effect = self._prep_properties
        connector._udm.add.side_effect = self._add
        mocker.patch.object(Connector, "source_search", self._source_search)

    def _list(self, model, primary_key, **kwargs):
        return dict(self.old_users if model == UDMModel.USER else self.old_groups)

    def _prep_properties(self, model, entry):
        primary_key = entry["univentionObjectIdentifier"][0].decode()
        return {
            "univentionObjectIdentifier": primary_key,
            "username": primary_key,
            "name": primary_key,
        }

    def _add(self, model, props, position):
        if props["univentionObjectIdentifier"] in self.failing:
            raise ValueError("UDM rejected entry")

    def _source_search(self, search_base, *args):
        if search_base.startswith("cn=groups"):
            if self.on_group_search is not None:
                self.on_group_search()
            if self.group_search_error is not None:
                raise self.group_search_error
            return iter(self.groups)
        return iter(self.users)


@pytest.fixture()
def connector(connector_yaml_path):
    config = ConnectorConfig(connector_yaml_path)
    config.src.user_base = "cn=users,o=source"
    config.src.group_base = "cn=groups,o=source"
    config.udm.max_deletion_ratio = None
    connector = Connector.__new__(Connector)
    connector._config = config
    connector._udm = mock.Mock()
    connector._force_deletions = False
    return connector


@pytest.fixture()
def source(connector, mocker):
    return FakeSource(connector, mocker)


@pytest.fixture()
def udm_client():
    client = UDMClient.__new__(UDMClient)
    client._url = "https://udm.example.test/udm"
    client._username = "admin"
    client._password = "secret"
    client._ca_cert = None
    client._skip_writes = False
    client._connect_timeout = 10
    client._read_timeout = 10
    client._req_count = defaultdict(lambda: defaultdict(int))
    client._status_count = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    return client


def test_build_info():
    assert sample("nubus_directory_importer_build_info", version=metrics.__version__) == 1.0


def test_successful_run_matches_log_summary(connector, source, caplog):
    source.users = source_entries("u", 5)
    source.groups = source_entries("g", 2)
    source.old_users = old_entries("u", 3)
    source.failing = {"u1", "u3"}
    runs_before = sample("nubus_directory_importer_runs_total", result="success")

    with caplog.at_level(logging.INFO):
        result = connector()

    assert result == (7, 3, 2)
    assert "Finished sync of 7 entries" in caplog.text
    assert "2 errors when processing source entries" in caplog.text
    assert "Removed 3 obsolete target entries" in caplog.text
    assert model_samples(USERS) == (5.0, 2.0, 3.0)
    assert model_samples(GROUPS) == (2.0, 0.0, 0.0)
    assert sample("nubus_directory_importer_runs_total", result="success") == runs_before + 1
    assert sample("nubus_directory_importer_last_run_success") == 1.0
    assert sample("nubus_directory_importer_last_success_timestamp_seconds") == sample(
        "nubus_directory_importer_last_run_timestamp_seconds",
    )
    assert sample("nubus_directory_importer_last_run_duration_seconds") >= 0.0


def test_consecutive_runs_replace_values(connector, source):
    source.users = source_entries("u", 5)
    source.groups = source_entries("g", 2)
    source.failing = {"u1"}
    connector()

    source.users = source_entries("u", 3)
    source.groups = []
    source.failing = set()
    connector()

    assert model_samples(USERS) == (3.0, 0.0, 0.0)
    assert model_samples(GROUPS) == (0.0, 0.0, 0.0)


def test_run_with_entry_errors_counts_as_success(connector, source):
    source.users = source_entries("u", 2)
    source.failing = {"u0", "u1"}

    connector()

    assert model_samples(USERS) == (2.0, 2.0, 0.0)
    assert sample("nubus_directory_importer_last_run_success") == 1.0
    assert sample("nubus_directory_importer_last_success_timestamp_seconds") == sample(
        "nubus_directory_importer_last_run_timestamp_seconds",
    )


@pytest.mark.parametrize(
    "error",
    [ReadSourceDirectoryError(), RuntimeError("unexpected")],
)
def test_aborted_run_drops_values_of_models_not_reached(connector, source, error):
    source.users = source_entries("u", 5)
    source.groups = source_entries("g", 20)
    source.old_groups = old_entries("g", 7)
    connector()
    last_success = sample("nubus_directory_importer_last_success_timestamp_seconds")
    failed_before = sample("nubus_directory_importer_runs_total", result="failed")

    source.users = source_entries("u", 4)
    source.group_search_error = error
    with pytest.raises(type(error)):
        connector()

    assert model_samples(USERS) == (4.0, 0.0, 0.0)
    assert model_samples(GROUPS) == (None, None, None)
    assert sample("nubus_directory_importer_runs_total", result="failed") == failed_before + 1
    assert sample("nubus_directory_importer_last_run_success") == 0.0
    assert sample("nubus_directory_importer_last_success_timestamp_seconds") == last_success
    assert sample("nubus_directory_importer_last_run_timestamp_seconds") > last_success


def test_values_are_published_at_the_end_of_the_run(connector, source):
    source.users = source_entries("u", 5)
    source.groups = source_entries("g", 2)
    connector()
    finished_at = sample("nubus_directory_importer_last_run_timestamp_seconds")

    seen_during_run = {}

    def capture():
        seen_during_run["users"] = model_samples(USERS)
        seen_during_run["finished_at"] = sample(
            "nubus_directory_importer_last_run_timestamp_seconds",
        )

    source.users = source_entries("u", 3)
    source.on_group_search = capture
    connector()

    assert seen_during_run == {"users": (5.0, 0.0, 0.0), "finished_at": finished_at}
    assert model_samples(USERS) == (3.0, 0.0, 0.0)


@pytest.mark.parametrize("status", [200, 409])
def test_udm_request_counts(udm_client, mocker, status):
    mocker.patch(
        "univention.directory_importer.udm.requests.request",
        return_value=mock.Mock(status_code=status, headers={}),
    )
    labels = {"method": UDMMethod.GET.value, "model": UDMModel.USER.value}
    requests_before = sample("nubus_directory_importer_udm_requests_total", **labels) or 0.0
    responses_before = (
        sample("nubus_directory_importer_udm_responses_total", status=str(status), **labels)
        or 0.0
    )

    udm_client.request(UDMMethod.GET, UDMModel.USER)

    assert (
        sample("nubus_directory_importer_udm_requests_total", **labels)
        == requests_before + 1
    )
    assert (
        sample("nubus_directory_importer_udm_responses_total", status=str(status), **labels)
        == responses_before + 1
    )


def test_http_endpoint():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    metrics.start_server(port, "127.0.0.1")

    with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=5) as resp:
        body = resp.read().decode()
    assert resp.status == 200
    assert "nubus_directory_importer_runs_total" in body
    assert "nubus_directory_importer_build_info" in body
