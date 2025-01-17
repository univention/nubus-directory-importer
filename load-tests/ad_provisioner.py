# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import ldap3

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
    user_count: int = 1000
    users_per_group: int = 100

    def validate(self):
        """Validate configuration parameters"""
        if not all([self.host, self.admin_dn, self.password, self.base_dn]):
            raise ValueError("All connection parameters must be provided")
        if not self.base_dn.startswith("DC="):
            raise ValueError("base_dn must start with DC=")
        if self.user_count < 1:
            raise ValueError("user_count must be positive")


class ADProvisioner:
    def __init__(self, config: ADConfig):
        self.config = config
        logger.info(
            f"Initializing ADProvisioner with host={config.host}, base_dn={config.base_dn}",
        )
        self.server = ldap3.Server(config.host, get_info=ldap3.ALL)
        self.conn = None

    def connect(self) -> None:
        """Establish connection to AD server"""
        try:
            logger.debug(f"Attempting to connect to AD server at {self.config.host}")
            self.conn = ldap3.Connection(
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

    def generate_test_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Generate test users and groups"""
        logger.debug("Starting test data generation")
        users = []
        groups = []

        # Calculate number of groups
        num_groups = max(1, self.config.user_count // self.config.users_per_group)
        logger.info(
            f"Will generate {num_groups} groups for {self.config.user_count} users",
        )

        # Generate groups
        for i in range(num_groups):
            group_name = f"group_{i}"
            groups.append(
                {
                    "cn": group_name,
                    "objectClass": ["top", "group"],
                    "description": f"Group {i}",
                },
            )
            logger.debug(f"Generated group data: {group_name}")

        # Generate users
        domain = self.config.base_dn.replace("DC=", "").replace(",", ".")
        logger.debug(f"Using domain: {domain} for user email addresses")

        for i in range(self.config.user_count):
            username = f"user{i}"
            email = f"{username}@{domain}"

            # Generate random profile picture data (100KB)
            profile_data = random.randbytes(102400)  # 100KB of random data

            user_data = {
                "objectClass": "user",
                "cn": username,
                "sn": f"User{i}",
                "givenName": f"Test{i}",
                "userPrincipalName": email,
                "mail": email,
                "thumbnailPhoto": profile_data,
            }
            users.append(user_data)
            logger.debug(f"Generated user data: {username}")

        logger.info(f"Generated data for {len(users)} users and {len(groups)} groups")
        return users, groups

    def _create_group(self, group: Dict) -> bool:
        """Create AD group"""
        dn = f"CN={group['cn']},CN=Users,{self.config.base_dn}"
        logger.debug(f"Attempting to create group at DN: {dn}")

        try:
            success = self.conn.add(dn, attributes=group)
            if success:
                logger.info(f"Created group: {group['cn']}")
            else:
                logger.error(
                    f"Failed to create group {group['cn']}: {self.conn.result}",
                )
            return success
        except Exception as e:
            logger.error(f"Error creating group {group['cn']}: {str(e)}", exc_info=True)
            return False

    def _create_user(self, user: Dict) -> bool:
        """Create AD user"""
        dn = f"CN={user['cn']},CN=Users,{self.config.base_dn}"
        logger.debug(f"Attempting to create user at DN: {dn}")

        try:
            logger.debug(f"User attributes: {', '.join(user.keys())}")
            success = self.conn.add(dn, attributes=user)

            if success:
                logger.info(f"Created user: {user['cn']}")
            else:
                logger.error(f"Failed to create user {dn}: {self.conn.result}")

            # Add user to group after creation
            if success:
                group_num = int(user["cn"].replace("user", "")) % (
                    self.config.user_count // self.config.users_per_group
                )
                group_dn = f"CN=group_{group_num},CN=Users,{self.config.base_dn}"

                logger.debug(f"Adding user {user['cn']} to group: {group_dn}")
                mod_success = self.conn.modify(
                    group_dn,
                    {"member": [(ldap3.MODIFY_ADD, [dn])]},
                )

                if not mod_success:
                    logger.error(f"Failed to add user to group: {self.conn.result}")

            return success
        except Exception as e:
            logger.error(f"Error creating user {user['cn']}: {str(e)}", exc_info=True)
            return False

    def provision_directory(self) -> None:
        """Main provisioning method"""
        try:
            users, groups = self.generate_test_data()

            # Create groups first
            logger.info(f"Creating {len(groups)} groups...")
            groups_created = 0
            for group in groups:
                if self._create_group(group):
                    groups_created += 1
            logger.info(f"Successfully created {groups_created} groups")

            # Then create users
            logger.info(f"Creating {len(users)} users...")
            users_created = 0
            for user in users:
                if self._create_user(user):
                    users_created += 1
            logger.info(f"Successfully created {users_created} users")

            logger.info("Directory provisioning completed")

        except Exception:
            logger.error("Directory provisioning failed", exc_info=True)
            raise


def main():
    """Main entry point"""
    import argparse

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
        "--users-per-group",
        type=int,
        default=100,
        help="Users per group",
    )

    args = parser.parse_args()
    logger.debug(f"Parsed arguments: {args}")

    try:
        config = ADConfig(
            host=args.host,
            admin_dn=args.admin_dn,
            password=args.password,
            base_dn=args.base_dn,
            user_count=args.user_count,
            users_per_group=args.users_per_group,
        )

        provisioner = ADProvisioner(config)
        provisioner.connect()
        provisioner.provision_directory()

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
