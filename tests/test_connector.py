# -*- coding: utf-8 -*-
"""
Automatic tests for module udm_directory_connector.connector

Tests require OpenLDAP to be installed
"""

import os
import logging
import unittest

import ldap
from ldapurl import LDAPUrl
from ldap.ldapobject import ReconnectLDAPObject
from slapdtest import SlapdObject, SlapdTestCase

from udm_directory_connector import gen_password
from udm_directory_connector.config import ConnectorConfig
from udm_directory_connector.connector import Connector
from udm_directory_connector.udm import UDMMethod, UDMModel


# a template string for generating simple slapd.d file
SLAPD_CONF_TEMPLATE = r"""dn: cn=config
objectClass: olcGlobal
cn: config
olcServerID: %(serverid)s
olcLogLevel: %(loglevel)s
olcAuthzRegexp: {0}"gidnumber=%(root_gid)s\+uidnumber=%(root_uid)s,cn=peercred,cn=external,cn=auth" "%(rootdn)s"
olcTLSCACertificateFile: %(cafile)s
olcTLSCertificateFile: %(servercert)s
olcTLSCertificateKeyFile: %(serverkey)s
olcTLSVerifyClient: try

dn: cn=module,cn=config
objectClass: olcModuleList
cn: module
olcModuleLoad: back_%(database)s
olcModuleLoad: memberof
olcModuleLoad: refint
olcModuleLoad: unique

dn: olcDatabase=%(database)s,cn=config
objectClass: olcDatabaseConfig
objectClass: olcMdbConfig
olcDatabase: %(database)s
olcSuffix: %(suffix)s
olcRootDN: %(rootdn)s
olcRootPW: %(rootpw)s
olcDbDirectory: %(directory)s

"""

SLAPD_OVERLAYS_TEMPLATE = r"""dn: olcOverlay=unique,olcDatabase={1}%(database)s,cn=config
objectClass: olcOverlayConfig
objectClass: olcUniqueConfig
olcOverlay: unique
olcUniqueURI: serialize ldap:///%(suffix)s?uid,employeeNumber?sub?(objectClass=inetOrgPerson)
olcUniqueURI: serialize ldap:///%(suffix)s?cn?sub?(objectClass=groupOfNames)

dn: olcOverlay=refint,olcDatabase={1}%(database)s,cn=config
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
olcOverlay: refint
olcRefintAttribute: member
olcRefintNothing: cn=dummy

dn: olcOverlay=memberof,olcDatabase={1}%(database)s,cn=config
objectClass: olcOverlayConfig
objectClass: olcMemberOfConfig
olcMemberOfDangling: ignore
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf
olcMemberOfRefInt: TRUE
olcOverlay: memberof

"""


class ConnectorSlapd(SlapdObject):
    suffix = 'o=source'
    openldap_schema_files = (
        'core.ldif',
        'cosine.ldif',
        'inetorgperson.ldif',
        'nis.ldif',
        'tests/data/customADUser.ldif',
    )
    slapd_conf_template = SLAPD_CONF_TEMPLATE

    # def _write_config(self):
    #     SlapdObject._write_config(self)
    #     self.slapadd(
    #         SLAPD_OVERLAYS_TEMPLATE % {
    #             'database': self.database,
    #             'suffix': self.suffix,
    #         },
    #         ["-n0"],
    #     )


class TestUDMDirectoryConnector(SlapdTestCase):

    maxDiff = None

    ldap_object_class = ReconnectLDAPObject
    server_class = ConnectorSlapd

    @classmethod
    def setUpClass(cls):
        logging.getLogger().setLevel(os.environ.get('LOG_LEVEL', 'warn').upper())
        super().setUpClass()
        with open('tests/data/source.ldif', 'r', encoding='utf-8') as ldif_file:
            ldif_data = ldif_file.read()
        cls.num_ldif_entries = len([
            line
            for line in ldif_data.split('\n')
            if line.startswith('dn:')
        ])
        cls.server.ldapadd(ldif_data)
        cls.config = ConnectorConfig('tests/data/connector.yml')
        cls.connector = Connector(cls.config)
        cls.config.src.ldap_uri = LDAPUrl(cls.server.default_ldap_uri)

    def setUp(self):
        try:
            self._ldap_conn
        except AttributeError:
            # open local LDAP connection
            self._ldap_conn = self._open_ldap_conn(bytes_mode=False)

    def tearDown(self):
        del self._ldap_conn
        for model, primary_key, position in (
                (
                    UDMModel.USER,
                    self.connector._config.udm.user_primary_key_property,
                    f'{self.connector._config.udm.user_ou},{self.connector._udm.base_position}'
                ),
                (
                    UDMModel.GROUP,
                    self.connector._config.udm.group_primary_key_property,
                    f'{self.connector._config.udm.group_ou},{self.connector._udm.base_position}'
                ),
            ):
            try:
                entries = self.connector._udm.list(model, primary_key, position=position).values()
            except:
                pass
            else:
                for entry_dn, _ in entries:
                    try:
                        self.connector._udm.delete(model, entry_dn)
                    except:
                        pass

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        udm_client = cls.connector._udm
        udm_client.delete(UDMModel.OU, f'{cls.config.udm.user_ou},{udm_client.base_position}')
        udm_client.delete(UDMModel.OU, f'{cls.config.udm.group_ou},{udm_client.base_position}')

    def test000_local_conn(self):
        self.assertEqual(self._ldap_conn.whoami_s(), 'dn:cn=Manager,o=source')
        self.assertEqual(
            len(self._ldap_conn.search_s('o=source', ldap.SCOPE_SUBTREE, attrlist=['1.1'])),
            self.num_ldif_entries
        )

    def test001_connector_run(self):
        # this run adds new entries
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(source_results_count, 15)
        self.assertEqual(delete_count, 0)
        self.assertEqual(error_count, 0)
        # this run essentially does nothing to existing entries
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(delete_count, 0)
        self.assertEqual(error_count, 0)

        # modify naming attributes in source entry
        self._ldap_conn.modify_s(
            'uid=user-1,ou=dept-1,o=source',
            [
                (ldap.MOD_REPLACE, 'cn', [b'Foo Bar']),
                (ldap.MOD_REPLACE, 'sn', [b'Bar']),
                (ldap.MOD_REPLACE, 'mail', [b'Foo_Bar@example.org']),
            ],
        )
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(delete_count, 0)
        self.assertEqual(error_count, 0)
        # rename username of source entry

        self._ldap_conn.rename_s(
            'uid=user-1,ou=dept-1,o=source',
            'uid=user-1-foo',
            newsuperior='ou=dept-2,o=source',
            delold=1,
        )
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(delete_count, 0)
        self.assertEqual(error_count, 0)
        # rename name of source group entry
        self._ldap_conn.rename_s(
            'cn=group-odd-1,ou=dept-1,o=source',
            'cn=group-odd-1-foo',
            newsuperior='ou=dept-2,o=source',
            delold=1,
        )
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(delete_count, 0)
        self.assertEqual(error_count, 0)
        udm_res = self.connector._udm.request(UDMMethod.GET, UDMModel.GROUP, params=dict(filter='(cn=group-odd-1-foo)'))
        udm_json = udm_res.json()
        self.assertEqual(udm_json['results'], 1)
        self.assertEqual(udm_json['_embedded']['udm:object'][0]['properties']['name'], 'group-odd-1-foo')
        # delete source entry
        self._ldap_conn.delete_s('uid=user-1-foo,ou=dept-2,o=source')
        source_results_count, delete_count, error_count = self.connector()
        self.assertEqual(source_results_count, 14)
        self.assertEqual(delete_count, 1)
        self.assertEqual(error_count, 0)

    def test002_sync_jpeg_photo(self):
        # Get UniventionObjectIdentifier
        source_users = dict(
            self.connector.source_search(
                self.connector._config.src.user_base,
                self.connector._config.src.user_scope,
                self.connector._config.src.user_filter,
                self.connector._config.src.user_attrs,
                self.connector._config.src.user_range_attrs,
            )
        )
        user_univention_uuid = source_users['uid=user-2,ou=dept-1,o=source']['entryUUID'][0].decode()

        # Create user with jpeg photo set
        user_properties = {
            'username': 'user-2',
            'firstname': 'Klaus',
            'lastname': 'Tiede',
            'displayName': 'Bar Baz',
            'e-mail': ['Bar_Baz@example.org'],
            'mailPrimaryAddress': 'Bar_Baz@example.org',
            'univentionObjectIdentifier': user_univention_uuid,
            'password': gen_password(),
            'jpegPhoto': '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wgARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQBAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhADEAAAAX8P/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxB//9k=',
        }
        self.connector._udm.add(
            UDMModel.USER,
            user_properties,
            f'{self.connector._config.udm.user_ou},{self.connector._udm.base_position}',
        )

        # Synchronize LDIF with same user but with no jpegPhoto set
        source_results_count, delete_count, error_count = self.connector()

        self.assertEqual(error_count, 0)


if __name__ == '__main__':
    unittest.main()
