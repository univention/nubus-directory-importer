# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
from dataclasses import dataclass, field
from typing import Dict

import ldap3
from ldap3.core.connection import Connection

logger = logging.getLogger(__name__)


@dataclass
class ADConfig:
    """Configuration for AD connection and test data generation"""

    host: str
    admin_dn: str
    password: str
    base_dn: str
    groups: list[int] = field(default_factory=list)
    user_count: int = 1000
    name_prefix: str = ""

    def __post_init__(self):
        """Validate configuration parameters"""
        if not all([self.host, self.admin_dn, self.password, self.base_dn]):
            raise ValueError("All connection parameters must be provided")
        if not self.base_dn.startswith("DC="):
            raise ValueError("base_dn must start with DC=")
        if self.user_count < 1:
            raise ValueError("user_count must be positive")
        if not all(count > 0 for count in self.groups):
            raise ValueError("all group maximum user counts must be positive")


class ADConnection:
    def __init__(self, config: ADConfig):
        self.config = config
        logger.info(
            f"Initializing ADProvisioner with host={config.host}, base_dn={config.base_dn}",
        )
        self.users_created = 0
        self.groups_created = 0
        self.server = ldap3.Server(config.host, get_info=ldap3.ALL)
        self.conn = self.connect()

    def connect(self) -> Connection:
        """Establish connection to AD server"""
        try:
            logger.debug(f"Attempting to connect to AD server at {self.config.host}")
            conn = ldap3.Connection(
                self.server,
                user=self.config.admin_dn,
                password=self.config.password,
                authentication=ldap3.SIMPLE,
                auto_bind=True,
            )
            logger.info("Successfully connected to AD server")
            logger.debug(f"Server info: {self.server.info}")
        except Exception as e:
            logger.error(f"Failed to connect to AD: {str(e)}", exc_info=True)
            raise
        return conn

    def create_group(self, groupname: str, member: list[str]) -> bool:
        """Create AD group"""
        dn = self.dn_builder(groupname)
        member_dn = [self.dn_builder(username) for username in member]

        attributes = {
            "cn": groupname,
            "objectClass": ["top", "group"],
            "description": f"Group name: {groupname}",
            "sAMAccountName": groupname,
        }
        if member:
            attributes["member"] = member_dn

        logger.debug("Attempting to create group at DN: %s", dn)
        try:
            success = self.conn.add(dn, attributes=attributes)
            if not success:
                raise Exception(
                    f"Failed to create group {groupname}: {self.conn.result}",
                )
            logger.info(f"Created group: {groupname}")
            self.groups_created += 1
            logger.info(f"Successfully created {self.groups_created} groups")
            return success
        except Exception as e:
            logger.error(f"Error creating group {groupname}: {str(e)}", exc_info=True)
            raise

    def create_user(self, username: str, user: Dict) -> bool:
        """Create AD user"""
        dn = self.dn_builder(username)
        logger.debug(f"Attempting to create user at DN: {dn}")

        try:
            logger.debug(f"User attributes: {', '.join(user.keys())}")
            success = self.conn.add(dn, attributes=user)

            if not success:
                raise Exception(f"Failed to create user {dn}: {self.conn.result}")

            logger.info(f"Created user: {user['cn']}")

            self.users_created += 1
            logger.info(f"Successfully created {self.users_created} users")
            return success
        except Exception as e:
            logger.error(f"Error creating user {user['cn']}: {str(e)}", exc_info=True)
            raise

    def dn_builder(self, username: str) -> str:
        return f"CN={username},CN=Users,{self.config.base_dn}"
