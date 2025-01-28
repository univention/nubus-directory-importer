# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
from typing import Generator

import ldap3
import pytest
from src.ad_connection import ADConnection

from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import Connector

logger = logging.getLogger(__name__)


# CONNECTIONS


@pytest.fixture
def ad_connection(ad_config) -> Generator[ADConnection, None, None]:
    """Create AD connection for tests"""
    connection = ADConnection(ad_config)
    yield connection
    # No cleanup needed, VM will be reset after tests
    connection.conn.unbind()


@pytest.fixture
def ldap_connection(ldap_config) -> Generator[ldap3.Connection, None, None]:
    """Create LDAP connection for verification"""
    server = ldap3.Server(ldap_config["host"])
    connection = ldap3.Connection(
        server,
        user=ldap_config["admin_dn"],
        password=ldap_config["password"],
        authentication=ldap3.SIMPLE,
        auto_bind=ldap3.AUTO_BIND_NO_TLS,
    )
    yield connection
    connection.unbind()


# DIRECTORY IMPORTER


def trigger_sync(connector_config: ConnectorConfig) -> None:
    """Trigger the sync process between AD and LDAP using the Connector"""
    logger.info("Triggering sync between AD and LDAP")

    try:
        connector = Connector(connector_config)
        source_count, delete_count, error_count = connector()

        logger.info(
            "Sync completed - Processed: %d, Deleted: %d, Errors: %d",
            source_count,
            delete_count,
            error_count,
        )

        if error_count > 0:
            raise RuntimeError(f"Sync completed with {error_count} errors")

    except Exception as e:
        logger.error("Error during sync: %s", str(e))
        raise


# MISCELANEOUS


def ad_user(
    ad_connection: ADConnection,
    directory_importer_config,
    ldap_base_dn,
    faker,
    extra_attrs=None,
):
    """Create a test user in Active Directory"""
    user_name = f"user{faker.user_name()}"
    user_ad_dn = ad_connection.dn_builder(user_name)
    user_ldap_dn = (
        f"uid={user_name},{directory_importer_config.udm.user_ou},{ldap_base_dn}"
    )
    user_data = {
        "objectClass": "user",
        "cn": user_name,
        "sn": "Sync",
        "givenName": "Test",
        "mail": f"{user_name}@example.com",
        "sAMAccountName": user_name,
    }
    if extra_attrs:
        user_data.update(extra_attrs)
    ad_connection.create_user(user_name, user_data)
    return user_name, user_ad_dn, user_ldap_dn


def ad_group(
    ad_connection: ADConnection,
    directory_importer_config,
    ldap_base_dn,
    faker,
):
    """Create a test group in Active Directory"""
    group_name = faker.user_name()
    group_ad_dn = ad_connection.dn_builder(group_name)
    group_ldap_dn = (
        f"cn={group_name},{directory_importer_config.udm.group_ou},{ldap_base_dn}"
    )
    ad_connection.create_group(group_name, [])
    return group_name, group_ad_dn, group_ldap_dn


def verify_ldap_object(
    ldap_conn: ldap3.Connection,
    dn: str,
    expected_attrs: dict = {},
) -> bool:
    """Verify object exists in LDAP and optionally check its attributes"""
    ldap_conn.search(
        search_base=dn,
        search_filter="(objectClass=*)",
        attributes=["*"],
    )

    if not ldap_conn.entries:
        return False

    if expected_attrs:
        entry = ldap_conn.entries[0]
        return all(
            str(getattr(entry, attr, None)) == str(value)
            for attr, value in expected_attrs.items()
        )
    return True


# TESTS


def test_create_group_and_user(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    directory_importer_config,
    ldap_base_dn,
    faker,
):
    """Test creation of group and user, verify they appear in LDAP after sync"""

    _, _, group_ldap_dn = ad_group(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )
    _, _, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )

    trigger_sync(directory_importer_config)

    assert verify_ldap_object(
        ldap_connection,
        group_ldap_dn,
    ), "Group should be created in LDAP"
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should be created in LDAP"


def test_modify_user_property(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """Test modifying user property in AD and verify changes in LDAP"""
    _, user_ad_dn, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
        extra_attrs={"sn": "Initial"},
    )

    # Trigger sync with initial fields
    trigger_sync(directory_importer_config)

    # Verify initial state
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs={"sn": "Initial"},
    ), "User should initially have `initial` sn attribute"

    # Modify user in AD
    ad_connection.conn.modify(
        user_ad_dn,
        {"sn": [(ldap3.MODIFY_REPLACE, ["Updated"])]},
    )

    # Trigger sync with updated fields
    trigger_sync(directory_importer_config)

    # Verify in LDAP
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs={"sn": "Updated"},
    ), "User should have updated sn attribute to `Updated`"


def test_add_user_to_group(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """Test adding user to group in AD and verify membership in LDAP"""
    _, group_ad_dn, group_ldap_dn = ad_group(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )
    _, user_ad_dn, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )

    # Trigger sync with user not in group
    trigger_sync(directory_importer_config)

    # Verify initial state - user should not be in group
    ldap_connection.search(
        search_base=group_ldap_dn,
        search_filter="(objectClass=*)",
        attributes=["uniqueMember"],
    )
    assert ldap_connection.entries, "Group should exist in LDAP"
    initial_members = getattr(ldap_connection.entries[0], "uniqueMember", [])
    assert user_ldap_dn not in initial_members, "User should not be in group initially"

    # Add user to group in AD
    ad_connection.conn.modify(
        group_ad_dn,
        {"member": [(ldap3.MODIFY_ADD, [user_ad_dn])]},
    )

    # Trigger sync after adding user to group
    trigger_sync(directory_importer_config)

    # Verify user is now in group in LDAP
    ldap_connection.search(
        search_base=group_ldap_dn,
        search_filter="(objectClass=*)",
        attributes=["uniqueMember"],
    )
    assert ldap_connection.entries, "Group should exist in LDAP"
    updated_members = getattr(ldap_connection.entries[0], "uniqueMember", [])
    assert user_ldap_dn in updated_members, "User should be in group after modification"


def test_delete_user(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """Test deleting user in AD and verify removal from LDAP"""
    _, user_ad_dn, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )

    # Trigger sync to create the user in LDAP
    trigger_sync(directory_importer_config)

    # Ensure user exists in LDAP
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should be created in LDAP"

    # Delete user in AD
    ad_connection.conn.delete(user_ad_dn)

    # Trigger sync to remove user from LDAP
    trigger_sync(directory_importer_config)

    # Verify user is deleted from LDAP
    assert not verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should be deleted from LDAP"


def test_delete_group(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """Test deleting group in AD and verify removal from LDAP"""
    _, group_ad_dn, group_ldap_dn = ad_group(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )

    # Trigger sync to create the group in LDAP
    trigger_sync(directory_importer_config)

    # Ensure group exists in LDAP
    assert verify_ldap_object(
        ldap_connection,
        group_ldap_dn,
    ), "Group should be created in LDAP"

    # Delete group in AD
    ad_connection.conn.delete(group_ad_dn)

    # Trigger sync to remove group from LDAP
    trigger_sync(directory_importer_config)

    # Verify group is deleted from LDAP
    assert not verify_ldap_object(
        ldap_connection,
        group_ldap_dn,
    ), "Group should be deleted from LDAP"


def test_delete_group_with_users(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """Test deleting group with users in AD and verify removal from LDAP"""
    _, group_ad_dn, group_ldap_dn = ad_group(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )
    _, user_ad_dn, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
    )

    # Add user to group in AD
    ad_connection.conn.modify(
        group_ad_dn,
        {"member": [(ldap3.MODIFY_ADD, [user_ad_dn])]},
    )

    # Trigger sync to create the group and user in LDAP
    trigger_sync(directory_importer_config)

    # Ensure group and user exist in LDAP
    assert verify_ldap_object(
        ldap_connection,
        group_ldap_dn,
    ), "Group should be created in LDAP"
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should be created in LDAP"

    # Ensure user is in group
    ldap_connection.search(
        search_base=group_ldap_dn,
        search_filter="(objectClass=*)",
        attributes=["uniqueMember"],
    )
    assert ldap_connection.entries, "Group should exist in LDAP"
    initial_members = getattr(ldap_connection.entries[0], "uniqueMember", [])
    assert user_ldap_dn in initial_members, "User should be in group initially"

    # Delete group in AD
    ad_connection.conn.delete(group_ad_dn)

    # Trigger sync to remove group and user from LDAP
    trigger_sync(directory_importer_config)

    # Verify group is deleted from LDAP and user is not
    assert not verify_ldap_object(
        ldap_connection,
        group_ldap_dn,
    ), "Group should be deleted from LDAP"
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should not be deleted from LDAP"
