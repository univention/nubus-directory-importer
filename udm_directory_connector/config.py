# -*- coding: ascii -*-
"""
udm_directory_connector.config - parsing configuration
"""

import re
from typing import Sequence

import strictyaml
from strictyaml import (
    Bool,
    Enum,
    Float,
    Int,
    Map,
    MapPattern,
    Optional,
    Seq,
    Str,
)

import certifi

# from python-ldap package
from ldapurl import SEARCH_SCOPE, LDAPUrl

from junkaptor.trans import Transformer


__all__ = (
    'ConnectorConfig',
)


CFG_ENCODING = 'utf-8'

CFG_USER_ATTRS_DEFAULT = [
    'objectGUID',
    'entryUUID',
    'userPrincipalName',
    'cn',
    'givenName',
    'sn',
    'mail',
    'telephoneNumber',
    'mobile',
    'memberOf',
    'proxyAddresses',
]

CFG_GRP_ATTRS_DEFAULT = [
    'objectGUID',
    'entryUUID',
    'cn',
    'member',
]

CFG_USER_PROPS_DEFAULT = [
    'city',
    'country',
    'departmentNumber',
    'description',
    'e-mail',
    'employeeNumber',
    'employeeType',
    'firstname',
    'homePostalAddress',
    'homeTelephoneNumber',
    'initials',
    'jpegPhoto',
    'lastname',
    'mailPrimaryAddress',
    'mobileTelephoneNumber',
    'organisation',
    'phone',
    'physicalDeliveryOfficeName',
    'postOfficeBox',
    'postcode',
    'preferredDeliveryMethod',
    'preferredLanguage',
    'roomNumber',
    'secretary',
    'street',
    'title',
    'username',
    'univentionObjectIdentifier',
]

CFG_GROUP_PROPS_DEFAULT = [
    'name',
    'description',
    'users',
    'nestedGroup',
    'univentionObjectIdentifier',
]

CFG_SCHEMA_UDM = Map({
    'uri': Str(),
    'user': Str(),
    'password': Str(),
    Optional('ca_cert', default=certifi.where()): Str(),
    Optional('skip_writes', default=False): Bool(),
    Optional('connect_timeout', default=6.0): Float(),
    Optional('read_timeout', default=1800.0): Float(),
    'user_ou': Str(),
    Optional('user_primary_key_property', default='uniqueIdentifier'): Str(),
    Optional('user_properties', default=CFG_USER_PROPS_DEFAULT): Seq(Str()),
    'group_ou': Str(),
    Optional('group_primary_key_property', default='uniqueIdentifier'): Str(),
    Optional('group_properties', default=CFG_GROUP_PROPS_DEFAULT): Seq(Str()),
})

CFG_TRANSFORMER = Map({
    Optional(
        'sanitizer',
        default={
            'objectGUID': ['udm_directory_connector.sanitize:guid2uuid'],
            'telephoneNumber': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'mobile': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'mobileTelephoneNumber': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'homePhone': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'homeTelephoneNumber': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'facsimileTelephoneNumber': ['udm_directory_connector.sanitize:phone_sanitizer'],
            'fax': ['udm_directory_connector.sanitize:phone_sanitizer'],
            #'mail': ['udm_directory_connector.sanitize:mail_sanitizer'],
            #'mailPrimaryAddress': ['udm_directory_connector.sanitize:mail_sanitizer'],
            #'mailLocalAddress': ['udm_directory_connector.sanitize:mail_sanitizer'],
            #'mailAlternativeAddress': ['udm_directory_connector.sanitize:mail_sanitizer'],
        },
    ): MapPattern(Str(), Seq(Str())),
    Optional('fixed_attrs'): MapPattern(Str(), Seq(Str())),
    Optional('fallback_attrs'): MapPattern(Str(), Seq(Str())),
    Optional('rename_attrs'): MapPattern(Str(), Str()),
    Optional('compose_attrs'): MapPattern(Str(), Seq(Str())),
    Optional('remove_attrs'): Seq(Str()),
    Optional('remove_values'): MapPattern(Str(), Seq(Str())),
    Optional('recode_attrs'): MapPattern(Str(), Str()),
    Optional('replace_values'): MapPattern(Str(), MapPattern(Str(), Str())),
    Optional('decompose_attrs'): MapPattern(Str(), Seq(Str())),
})

CFG_SCHEMA_SOURCE_LDAP = Map({
    'ldap_uri': Str(),
    Optional('bind_dn'): Str(),
    Optional('bind_pw'): Str(),
    Optional('sasl_method'): Str(),
    Optional('ca_cert', default=certifi.where()): Str(),
    Optional('timeout', default=5.0): Float(),
    Optional('trace_level', default=0): Int(),
    Optional('search_pagesize', default=500): Int(),
    Optional('ignore_dn_regex'): Str(),
    'user_base': Str(),
    Optional('user_scope', default='sub'): Enum(('one', 'sub')),
    Optional('user_filter', default='(objectClass=user)'): Str(),
    Optional('user_attrs', default=CFG_USER_ATTRS_DEFAULT): Seq(Str()),
    Optional('user_range_attrs', default=['memberOf']): Seq(Str()),
    Optional('user_trans'): CFG_TRANSFORMER,
    'group_base': Str(),
    Optional('group_scope', default='sub'): Enum(('one', 'sub')),
    Optional('group_filter', default='(objectClass=group)'): Str(),
    Optional('group_attrs', default=CFG_GRP_ATTRS_DEFAULT): Seq(Str()),
    Optional('group_range_attrs', default=['member']): Seq(Str()),
    Optional('group_trans'): CFG_TRANSFORMER,
})

CFG_SCHEMA = Map({
    'udm': CFG_SCHEMA_UDM,
    'source': CFG_SCHEMA_SOURCE_LDAP,
})


class SourceConfig:
    """
    Model for a single source connector configuration
    """

    __slots__ = (
        '_yml',
        # Connection config
        'ldap_uri',
        'bind_dn',
        'bind_pw',
        'ca_cert',
        # Logging config
        'trace_level',
        # Performance config
        'timeout',
        'search_pagesize',
        # Functional config
        'user_base',
        'user_scope',
        'user_filter',
        'user_attrs',
        'user_range_attrs',
        'user_trans',
        'group_base',
        'group_scope',
        'group_filter',
        'group_attrs',
        'group_range_attrs',
        'group_trans',
    )

    ldap_uri: LDAPUrl
    bind_dn: str
    bind_pw: bytes
    ca_cert: str
    trace_level: int
    timeout: float
    search_pagesize: int
    user_base: str
    user_scope: int
    user_filter: str
    user_attrs: Sequence[str]
    user_range_attrs: Sequence[str]
    user_trans: Transformer
    group_base: str
    group_scope: int
    group_filter: str
    group_attrs: Sequence[str]
    group_range_attrs: Sequence[str]
    group_trans: Transformer

    def __init__(self, yml):
        self._yml = yml
        self.ldap_uri = LDAPUrl(yml['ldap_uri'].text)
        self.bind_dn = yml['bind_dn'].text
        self.bind_pw = yml['bind_pw'].text.encode('utf-8')
        self.ca_cert = yml['ca_cert'].text
        self.trace_level = yml['trace_level'].data
        self.timeout = yml['timeout'].data
        self.search_pagesize = yml['search_pagesize'].data
        self.user_base = yml['user_base'].text
        self.user_scope = SEARCH_SCOPE[yml['user_scope'].text]
        self.user_filter = yml['user_filter'].text
        self.user_attrs = yml['user_attrs'].data
        self.user_range_attrs = yml['user_range_attrs'].data
        self.user_trans = Transformer(**self._yml['user_trans'].data)
        self.group_base = yml['group_base'].text
        self.group_scope = SEARCH_SCOPE[yml['group_scope'].text]
        self.group_filter = yml['group_filter'].text
        self.group_attrs = yml['group_attrs'].data
        self.group_range_attrs = yml['group_range_attrs'].data
        self.group_trans = Transformer(**self._yml['group_trans'].data)

    @property
    def ignore_dn_regex(self):
        val = self._yml.get('ignore_dn_regex', None)
        if val is not None:
            val = re.compile(val.text)
        return val


class UDMConfig:
    """
    UDM configuration parameter class
    """

    __slots__ = (
        '_yml',
        # Connection config
        'uri',
        'user',
        'password',
        'ca_cert',
        # debug config
        'skip_writes',
        # Performance config
        'connect_timeout',
        'read_timeout',
        # Functional config
        'user_ou',
        'user_primary_key_property',
        'user_properties',
        'group_ou',
        'group_primary_key_property',
        'group_properties',
    )

    uri: str
    user: str
    password: str
    ca_cert: str
    skip_writes: bool
    timeout: float
    user_ou: str
    group_ou: str
    user_primary_key_property: str
    group_primary_key_property: str

    def __init__(self, yml):
        self._yml = yml
        self.uri = yml['uri'].text
        self.user = yml['user'].text
        self.password = yml['password'].text
        self.ca_cert = yml['ca_cert'].text
        self.skip_writes = yml['skip_writes'].data
        self.connect_timeout = yml['connect_timeout'].data
        self.read_timeout = yml['read_timeout'].data
        self.user_ou = yml['user_ou'].text
        self.user_primary_key_property = yml['user_primary_key_property'].text
        self.user_properties = set(yml['user_properties'].data)
        self.group_ou = yml['group_ou'].text
        self.group_primary_key_property = yml['group_primary_key_property'].text
        self.group_properties = set(yml['group_properties'].data)


class ConnectorConfig:
    """
    Model for the complete connector configuration
    """

    __slots__ = (
        'state',
        'src',
        'udm',
    )

    src: SourceConfig
    udm: UDMConfig

    def __init__(self, config_filename):
        with open(config_filename, 'r', encoding=CFG_ENCODING) as config_file:
            yml = strictyaml.load(config_file.read(), CFG_SCHEMA)
        self.src = SourceConfig(yml['source'])
        self.udm = UDMConfig(yml['udm'])
