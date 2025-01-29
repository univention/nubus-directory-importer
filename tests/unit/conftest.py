# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest
import requests

from univention.directory_importer.config import ConnectorConfig


@pytest.fixture(scope="session")
def directory_importer_config():
    return ConnectorConfig("tests/data/connector.yml")


@pytest.fixture(scope="session", autouse=True)
def maildomain(directory_importer_config: ConnectorConfig):
    base_url = f"{directory_importer_config.udm.uri}mail/domain/"
    auth = (directory_importer_config.udm.user, directory_importer_config.udm.password)
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    create_response = requests.post(
        base_url,
        auth=auth,
        headers=headers,
        json={
            "properties": {
                "name": "example.org",
                "objectFlag": [],
            },
            "position": "cn=domain,cn=mail,dc=univention-organization,dc=intranet",
        },
    )
    assert (
        create_response.status_code == 201
    ), f"Failed to create domain: {create_response.status_code}, {create_response.text}"

    yield create_response.json()

    delete_response = requests.delete(
        f"{base_url}cn=example.org,cn=domain,cn=mail,dc=univention-organization,dc=intranet",
        auth=auth,
        headers=headers,
    )
    assert (
        delete_response.status_code == 204
    ), f"Failed to delete domain: {delete_response.status_code}, {delete_response.text}"
