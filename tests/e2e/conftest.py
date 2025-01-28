# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
import random

import pytest
from src.ad_connection import ADConfig

from univention.directory_importer.config import ConnectorConfig

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    # Connector configuration
    parser.addoption(
        "--connector-config",
        default="tests/e2e/importer-config.yaml",
        help="Path to connector configuration YAML file",
    )

    # AD configuration
    parser.addoption(
        "--ad-base-dn",
        default="DC=ad,DC=test",
        help="Base DN for Active Directory.",
    )

    # LDAP configuration
    parser.addoption("--ldap-host", default="ldap-server", help="Host for LDAP.")
    parser.addoption(
        "--ldap-admin-dn",
        default="cn=admin,dc=univention-organization,dc=intranet",
        help="Admin DN for LDAP.",
    )
    parser.addoption(
        "--ldap-base-dn",
        default="dc=univention-organization,dc=intranet",
        help="Base DN for LDAP.",
    )

    # Random seed
    parser.addoption("--randomly-seed", help="Seed to use for randomization.")


# CONFIGURATIONS
@pytest.fixture(scope="session")
def ad_config(pytestconfig, directory_importer_config) -> ADConfig:
    """Provide AD configuration for tests"""
    return ADConfig(
        host=directory_importer_config.src.ldap_uri.hostport,
        admin_dn=directory_importer_config.src.bind_dn,
        password=directory_importer_config.src.bind_pw,
        base_dn=pytestconfig.option.ad_base_dn,
    )


@pytest.fixture(scope="session")
def ldap_config(pytestconfig, directory_importer_config) -> dict:
    """Provide LDAP configuration for tests"""
    return {
        "host": pytestconfig.option.ldap_host,
        "admin_dn": pytestconfig.option.ldap_admin_dn,
        "password": directory_importer_config.udm.password,
        "base_dn": pytestconfig.option.ldap_base_dn,
    }


@pytest.fixture(scope="session")
def directory_importer_config(pytestconfig) -> ConnectorConfig:
    return ConnectorConfig(pytestconfig.option.connector_config)


@pytest.fixture(scope="session")
def ldap_base_dn(pytestconfig) -> str:
    """Provide LDAP base DN for tests"""
    return pytestconfig.option.ldap_base_dn


def udm_config(pytestconfig) -> dict:
    """Provide UDM configuration for tests"""
    return {
        "host": pytestconfig.option.udm_host,
        "username": pytestconfig.option.udm_username,
        "password": pytestconfig.option.udm_password,
    }


# RANDOMIZATION


@pytest.fixture(scope="session")
def base_seed(pytestconfig) -> int:
    """
    Interim solution to randomize the integrated Faker.

    Long term we aim to go for ``pytest-randomly``.
    """
    base_seed = pytestconfig.getoption("--randomly-seed")
    if not base_seed:
        base_seed = random.randint(1000, 9999)
    print("base seed: ", base_seed)
    return base_seed


@pytest.fixture(scope="function", autouse=True)
def faker_seed(base_seed, request):
    """
    Generates unique but deterministic seeds for every test function.
    Based on a root seed and the test function name.

    When faker is used in a fixture that is used by multiple test functions.
    Each function expects different faker data.
    This is essential to avoid cross-contamination between tests
    because of test objects like LDAP users or groups.
    At the same time, the faker seed needs to stay deterministic.
    """
    test_function_name = request.node.name
    if hasattr(request, "param"):
        seed = f"{base_seed}-{test_function_name}-{request.param}"
    else:
        seed = f"{base_seed}-{test_function_name}"
    logger.info("Generated faker seed unique to the test function is: %s", seed)
    return seed
