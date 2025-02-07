# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import argparse
import logging
import random

from src.ad_connection import ADConfig, ADConnection  # noqa: E402
from src.ad_group import Group  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
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
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete all existing users and groups in AD. (cleanup)",
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
        delete=args.delete,
    )


def main():
    """Main entry point"""
    try:
        config = parse_args()
    except ValueError as error:
        logger.error(f"Error: {str(error)}", exc_info=True)
        raise SystemExit(1)

    connection = ADConnection(config)

    if config.delete:
        for entry in connection.get_entries_by_prefix(
            config.name_prefix,
            attributes=[],
            page_size=500,
        ):
            connection.delete_entry(entry["dn"])
        return

    logger.debug("Starting test data generation")

    groups: list[Group] = []
    # Configure groups
    for index, max_size in enumerate(config.groups):
        groupname = f"{config.name_prefix}_group-{index}_max-members-{max_size}"
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

    for group in groups:
        group.create()

    logger.info("Directory provisioning completed")


if __name__ == "__main__":
    main()
