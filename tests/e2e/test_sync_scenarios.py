# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
from typing import Generator

import ldap3
import pytest
from src.ad_connection import ADConnection

from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.connector import Connector, DeletionsBlockedError

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


def trigger_sync(connector_config: ConnectorConfig) -> tuple[int, int, int]:
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

    return source_count, delete_count, error_count


# MISCELANEOUS


def ad_user(
    ad_connection: ADConnection,
    directory_importer_config,
    ldap_base_dn,
    faker,
    extra_attrs=None,
    user_name=None,
):
    """Create a test user in Active Directory"""
    user_name = user_name or f"user{faker.user_name()}"
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
        "description": "False",
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
        logger.debug("LDAP entry not found: %s", dn)
        return False

    if expected_attrs:
        entry = ldap_conn.entries[0]
        logger.debug(
            "LDAP entry %s attributes: %s",
            dn,
            {attr: str(getattr(entry, attr, None)) for attr in entry.entry_attributes},
        )
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


def test_user_extended_attribute(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    directory_importer_config,
    ldap_base_dn,
    faker,
):
    """Test creation of a user, verify they appear in LDAP after sync"""

    _, _, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
        {"description": "True"},
    )

    trigger_sync(directory_importer_config)

    assert verify_ldap_object(ldap_connection, user_ldap_dn), (
        f"User not found in LDAP at {user_ldap_dn}"
    )
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs={"isOxUser": "OK"},
    ), "User found in LDAP but isOxUser is not OK"


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


def test_recreate_user_with_same_username(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    faker,
    directory_importer_config,
    ldap_base_dn,
):
    """
    Create a user, delete it and add it again under the same username.

    The last step deletes and re-creates the user without an intervening
    sync, so a single run sees both the obsolete entry and its replacement.
    That run has to release the username of the obsolete entry before the new
    entry is created, otherwise the username and its DN are still taken and
    the run fails.
    """
    user_name = f"user{faker.user_name()}".lower()
    expected_attrs = {"uid": user_name}

    _, user_ad_dn, user_ldap_dn = ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
        user_name=user_name,
    )

    # create the user
    _, _, error_count = trigger_sync(directory_importer_config)
    assert error_count == 0, "Initial sync must not report errors"
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs=expected_attrs,
    ), "User should be created in LDAP with its username"

    # delete the user
    ad_connection.conn.delete(user_ad_dn)
    _, delete_count, error_count = trigger_sync(directory_importer_config)
    assert error_count == 0, "Sync after deletion must not report errors"
    assert delete_count >= 1, "The user should have been removed from LDAP"
    assert not verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
    ), "User should be deleted from LDAP"

    # add the user again
    ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
        user_name=user_name,
    )
    _, _, error_count = trigger_sync(directory_importer_config)
    assert error_count == 0, "Re-adding the user must not report errors"
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs=expected_attrs,
    ), "User should be created in LDAP again with its username"

    # delete and add the user again without an intervening sync
    ad_connection.conn.delete(user_ad_dn)
    ad_user(
        ad_connection,
        directory_importer_config,
        ldap_base_dn,
        faker,
        user_name=user_name,
    )
    _, _, error_count = trigger_sync(directory_importer_config)
    assert error_count == 0, (
        "Deleting and re-adding a user with the same username "
        "within a single run must not report errors"
    )
    assert verify_ldap_object(
        ldap_connection,
        user_ldap_dn,
        expected_attrs=expected_attrs,
    ), "User should exist in LDAP with its original username"


def test_deletion_limit_blocks_sync(
    ad_connection: ADConnection,
    ldap_connection: ldap3.Connection,
    pytestconfig,
    directory_importer_config,
    ldap_base_dn,
    faker,
):
    """
    Test that the deletion safeguard blocks sync when the number of removals
    exceeds the configured limit, and that --force-deletions overrides it.

    Uses max_deletions=1 (absolute cap) so the assertion is deterministic
    regardless of how many other entries already exist in the environment.
    """
    # Create 3 users and sync them into LDAP
    users = [
        ad_user(ad_connection, directory_importer_config, ldap_base_dn, faker)
        for _ in range(3)
    ]
    trigger_sync(directory_importer_config)
    for _, _, user_ldap_dn in users:
        assert verify_ldap_object(ldap_connection, user_ldap_dn), (
            "All users must exist in LDAP before testing the limit"
        )

    # Remove 2 users from AD — exceeds the cap of 1
    for _, user_ad_dn, _ in users[:2]:
        ad_connection.conn.delete(user_ad_dn)

    # Sync with max_deletions=1: 2 removals > 1 → blocked
    limited_config = ConnectorConfig(pytestconfig.option.connector_config)
    limited_config.udm.max_deletions = 1
    limited_config.udm.max_deletion_ratio = None

    with pytest.raises(DeletionsBlockedError):
        Connector(limited_config)()

    # Both removed users must still exist in LDAP
    for _, _, user_ldap_dn in users[:2]:
        assert verify_ldap_object(ldap_connection, user_ldap_dn), (
            "Users must not be deleted from LDAP when the deletion limit is exceeded"
        )

    # --force-deletions overrides the safeguard: both users are now removed
    Connector(limited_config, force_deletions=True)()

    for _, _, user_ldap_dn in users[:2]:
        assert not verify_ldap_object(ldap_connection, user_ldap_dn), (
            "Users must be deleted from LDAP when force-deletions is used"
        )
