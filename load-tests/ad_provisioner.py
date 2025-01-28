# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import argparse
import logging
import random
from dataclasses import dataclass, field
from typing import Callable, Dict

import ldap3
from ldap3.core.connection import Connection

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

# Add file handler for persistent logging
file_handler = logging.FileHandler("ad_provisioner.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    ),
)
logger.addHandler(file_handler)


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
        """Validate the configuration parameters"""
        """Validate configuration parameters"""
        if not all([self.host, self.admin_dn, self.password, self.base_dn]):
            raise ValueError("All connection parameters must be provided")
        if not self.base_dn.startswith("DC="):
            raise ValueError("base_dn must start with DC=")
        if self.user_count < 1:
            raise ValueError("user_count must be positive")
        if not all(count > 0 for count in self.groups):
            raise ValueError("all group maximum user counts must be positive")


class Group:
    def __init__(
        self,
        name_prefix: str,
        size: int,
        create_group_callback: Callable[[str, list[str]], bool],
    ) -> None:
        self.name_prefix = name_prefix
        self.size = size
        self.create_group_callback = create_group_callback
        self.users_counter = 0
        self.users = []
        self.group_counter = 0

    def add(self, username: str) -> None:
        self.users.append(username)
        self.users_counter += 1

        if self.users_counter < self.size:
            return

        self.create(self.users)
        self.users_counter = 0
        self.users = []

    def create(self, users: list[str]) -> None:
        self.group_counter += 1
        name = f"{self.name_prefix}_{self.group_counter}"
        logger.debug("creating group: %s\n with users %s", name, users)

        self.create_group_callback(name, users)


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

        group = (
            {
                "cn": groupname,
                "objectClass": ["top", "group"],
                "description": f"Group name: {groupname}",
                "member": member_dn,
            },
        )

        logger.debug(f"Attempting to create group at DN: {dn}")

        try:
            success = self.conn.add(dn, attributes=group)
            if success:
                logger.info(f"Created group: {groupname}")
                self.groups_created += 1
                logger.info(f"Successfully created {self.groups_created} groups")
                return success
            logger.error(
                f"Failed to create group {groupname}: {self.conn.result}",
            )
        except Exception as e:
            logger.error(f"Error creating group {groupname}: {str(e)}", exc_info=True)
            raise
            return False

    def create_user(self, username: str, user: Dict) -> bool:
        """Create AD user"""
        dn = self.dn_builder(username)
        logger.debug(f"Attempting to create user at DN: {dn}")

        try:
            logger.debug(f"User attributes: {', '.join(user.keys())}")
            success = self.conn.add(dn, attributes=user)

            if success:
                logger.info(f"Created user: {user['cn']}")
            else:
                logger.error(f"Failed to create user {dn}: {self.conn.result}")

            self.users_created += 1
            logger.info(f"Successfully created {self.users_created} users")
            return success
        except Exception as e:
            logger.error(f"Error creating user {user['cn']}: {str(e)}", exc_info=True)
            raise
            return False

    def dn_builder(self, username: str) -> str:
        return f"CN={username},CN=Users,{self.config.base_dn}"


def parse_args() -> ADConfig:
    parser = argparse.ArgumentParser(
        description="Provision Active Directory with test data",
    )
    parser.add_argument("--host", required=True, help="AD host")
    parser.add_argument("--admin-dn", required=True, help="Admin DN")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--base-dn", required=True, help="Base DN")
    parser.add_argument(
        "--user-count",
        type=int,
        default=1000,
        help="Number of users to create",
    )
    parser.add_argument(
        "--group-with-max-users",
        type=int,
        action="append",
        help="Adds a group to every user. a minimum of one and a maximum of 20 groups can be specified."
        "Specify the maximum group size as an integer.",
    )
    parser.add_argument(
        "--name-prefix",
        default="",
        help="Prefix for all user and group names to avoid collisions",
    )

    args = parser.parse_args()
    logger.debug(f"Parsed arguments: {args}")

    return ADConfig(
        host=args.host,
        admin_dn=args.admin_dn,
        password=args.password,
        base_dn=args.base_dn,
        user_count=args.user_count,
        groups=args.group_with_max_users,
        name_prefix=args.name_prefix,
    )


def main():
    """Main entry point"""
    try:
        config = parse_args()
    except ValueError as error:
        logger.error(f"Error: {str(error)}", exc_info=True)
        raise SystemExit(1)

    connection = ADConnection(config)

    logger.debug("Starting test data generation")

    groups: list[Group] = []
    # Configure groups
    for index, max_size in enumerate(config.groups):
        groupname = f"{config.name_prefix}_g{index}m{max_size}"
        groups.append(Group(groupname, max_size, connection.create_group))

    # Generate users
    domain = config.base_dn.replace("DC=", "").replace(",", ".")
    logger.debug(f"Using domain: {domain} for user email addresses")

    for index in range(config.user_count):
        username = f"{config.name_prefix}_user_{index}"
        email = f"{username}@{domain}"

        # Generate random profile picture data (100KB)
        profile_data = random.randbytes(102400)  # 100KB of random data

        user_data = {
            "objectClass": "user",
            "cn": username,
            "sn": f"User{index}",
            "givenName": f"Test{index}",
            "userPrincipalName": email,
            "mail": email,
            "thumbnailPhoto": profile_data,
        }
        logger.debug(f"Generated user data: {username}")

        result = connection.create_user(username, user_data)
        if result is False:
            continue

        for group in groups:
            group.add(username)

    logger.info("Directory provisioning completed")


if __name__ == "__main__":
    main()
