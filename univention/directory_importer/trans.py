# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.trans - customer Transformer classes
"""

import logging

from junkaptor import decode_list
from junkaptor.trans import Transformer


class MemberRefsTransformer(Transformer):
    """
    Transformer class for sanitizing group member references
    based on primary key
    """

    __slots__ = (
        "_user_primary_key",
        "_group_primary_key",
        "_users",
        "_groups",
        "_id2dn_users",
        "_id2dn_groups",
        "_user_srckey_attr",
        "_group_srckey_attr",
        "_user_sanitizer",
        "_group_sanitizer",
        "_user_trans",
        "_group_trans",
    )

    def __init__(
        self,
        user_primary_key,
        user_trans,
        users,
        id2dn_users,
        group_primary_key,
        group_trans,
        groups,
        id2dn_groups,
    ):
        self._user_primary_key = user_primary_key
        self._user_trans = user_trans
        self._users = users
        self._id2dn_users = id2dn_users
        self._user_srckey_attr = user_trans._rename_attrs[user_primary_key]
        logging.debug("_user_srckey_attr = %r", self._user_srckey_attr)
        self._user_sanitizer = user_trans._sanitizer.get(
            self._user_srckey_attr,
            [lambda x: x],
        )[0]
        logging.debug("_user_sanitizer = %r", self._user_sanitizer)
        self._group_primary_key = group_primary_key
        self._group_trans = group_trans
        self._groups = groups
        self._id2dn_groups = id2dn_groups
        self._group_srckey_attr = group_trans._rename_attrs[group_primary_key]
        logging.debug("_group_srckey_attr = %r", self._group_srckey_attr)
        self._group_sanitizer = group_trans._sanitizer.get(
            self._group_srckey_attr,
            [lambda x: x],
        )[0]
        logging.debug("_group_sanitizer = %r", self._group_sanitizer)

    def __call__(self, record):
        members = decode_list(record.get("users", []))
        record["nestedGroup"] = []
        for member in members:
            if member in self._groups:
                primary_key = None
                try:
                    source_val = self._group_sanitizer(
                        self._groups[member][self._group_srckey_attr][0],
                    )
                    primary_key = source_val.decode("utf-8")
                    record["nestedGroup"].append(
                        self._id2dn_groups[primary_key].encode("utf-8"),
                    )
                except KeyError as err:
                    logging.warning(
                        "Error mapping %s - %s: %r",
                        member,
                        primary_key,
                        err,
                    )
        record["users"] = []
        for member in members:
            if member in self._users:
                primary_key = None
                try:
                    source_val = self._user_sanitizer(
                        self._users[member][self._user_srckey_attr][0],
                    )
                    primary_key = source_val.decode("utf-8")
                    record["users"].append(
                        self._id2dn_users[primary_key].encode("utf-8"),
                    )
                except KeyError as err:
                    logging.warning(
                        "Error mapping %s - %s: %r",
                        member,
                        primary_key,
                        err,
                    )
        return record
