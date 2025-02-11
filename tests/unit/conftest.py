# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest


@pytest.fixture()
def connector_yaml_path():
    return "tests/data/connector.yml"
