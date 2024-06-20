# -*- coding: ascii -*-
"""
udm_directory_connector.trans - customer Transformer classes
"""

import logging

from junkaptor.trans import Transformer
from junkaptor import decode_list


class MemberRefsTransformer(Transformer):
    """
    Transformer class for sanitizing group member references
    based on primary key
    """

    __slots__ = (
        '_user_pkey',
        '_group_pkey',
        '_users',
        '_groups',
        '_id2dn_users',
        '_id2dn_groups',
        '_user_srckey_attr',
        '_group_srckey_attr',
        '_user_sanitizer',
        '_group_sanitizer',
        '_user_trans',
        '_group_trans',
    )

    def __init__(
            self,
            user_pkey, user_trans, users, id2dn_users,
            group_pkey, group_trans, groups, id2dn_groups,
        ):
        self._user_pkey = user_pkey
        self._user_trans = user_trans
        self._users = users
        self._id2dn_users = id2dn_users
        self._user_srckey_attr = user_trans._rename_attrs[user_pkey]
        logging.debug('_user_srckey_attr = %r', self._user_srckey_attr)
        self._user_sanitizer = user_trans._sanitizer.get(self._user_srckey_attr, [lambda x: x])[0]
        logging.debug('_user_sanitizer = %r', self._user_sanitizer)
        self._group_pkey = group_pkey
        self._group_trans = group_trans
        self._groups = groups
        self._id2dn_groups = id2dn_groups
        self._group_srckey_attr = group_trans._rename_attrs[group_pkey]
        logging.debug('_group_srckey_attr = %r', self._group_srckey_attr)
        self._group_sanitizer = group_trans._sanitizer.get(self._group_srckey_attr, [lambda x: x])[0]
        logging.debug('_group_sanitizer = %r', self._group_sanitizer)

    def __call__(self, record):
        members = decode_list(record.get('users', []))
        record['nestedGroup'] = []
        for member in members:
            if member in self._groups:
                pkey = None
                try:
                    src_val = self._group_sanitizer(self._groups[member][self._group_srckey_attr][0])
                    pkey = src_val.decode('utf-8')
                    record['nestedGroup'].append(
                      self._id2dn_groups[pkey].encode('utf-8')
                    )
                except KeyError as err:
                    logging.warning('Error mapping %s - %s: %r', member, pkey, err)
        record['users'] = []
        for member in members:
            if member in self._users:
                pkey = None
                try:
                    src_val = self._user_sanitizer(self._users[member][self._user_srckey_attr][0])
                    pkey = src_val.decode('utf-8')
                    record['users'].append(
                      self._id2dn_users[pkey].encode('utf-8')
                    )
                except KeyError as err:
                    logging.warning('Error mapping %s - %s: %r', member, pkey, err)
        return record
