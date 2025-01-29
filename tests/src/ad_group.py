# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
from typing import Callable

logger = logging.getLogger(__name__)


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

        self.create()
        self.users_counter = 0
        self.users = []

    def create(self) -> None:
        if len(self.users) == 0:
            logger.warning(
                "Not creating a new group with prefix: %s because it currently has no members",
            )
        self.group_counter += 1
        name = f"{self.name_prefix}_{self.group_counter}"
        logger.debug("creating group: %s\n with users %s", name, self.users)

        self.create_group_callback(name, self.users)
