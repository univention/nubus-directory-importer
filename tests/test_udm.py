# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
Automatic tests for module univention.directory_importer.udm
"""

# from Python's standard lib
import copy
import logging
import os
import string
import unittest
import uuid
from http import HTTPStatus

import ldap.dn

from univention.directory_importer import gen_password, random_str
from univention.directory_importer.config import ConnectorConfig
from univention.directory_importer.udm import UDMClient, UDMMethod, UDMModel

CONNECTOR_CFG = ConnectorConfig("tests/data/connector.yml")


def init_udm_client(config):
    udm_config = config.udm
    return UDMClient(
        udm_config.uri,
        udm_config.user,
        udm_config.password,
        udm_config.user_ou,
        udm_config.group_ou,
        ca_cert=udm_config.ca_cert,
    )


class TestUDMClient(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "warn").upper())
        super(TestUDMClient, cls).setUpClass()
        udm_client = init_udm_client(CONNECTOR_CFG)
        cls.user_position = f"{CONNECTOR_CFG.udm.user_ou},{udm_client.base_position}"
        cls.group_position = f"{CONNECTOR_CFG.udm.group_ou},{udm_client.base_position}"

    @classmethod
    def tearDownClass(cls):
        super(TestUDMClient, cls).tearDownClass()
        udm_client = init_udm_client(CONNECTOR_CFG)
        udm_client.delete(UDMModel.OU, cls.user_position)
        udm_client.delete(UDMModel.OU, cls.group_position)

    @property
    def udm_client(self):
        return init_udm_client(CONNECTOR_CFG)

    # TODO: Administrator account is not present in the docker compose ldap server
    # def test001_search_administrator(self):
    #     udm_res = self.udm_client.user_query('lastname', 'Administrator')
    #     udm_json = udm_res.json()
    #     self.assertEqual(udm_json['results'], 1)
    #     udm_search_results = udm_json['_embedded']['udm:object']
    #     self.assertEqual(len(udm_search_results), 1)
    #     self.assertEqual(udm_search_results[0]['properties']['lastname'], 'Administrator')
    #     self.assertEqual(udm_search_results[0]['id'], 'Administrator')
    #     self.assertEqual(
    #         udm_search_results[0]['dn'],
    #         'uid=Administrator,' + udm_search_results[0]['position']
    #     )
    #     udm_res = self.udm_client.request(UDMMethod.GET, UDMModel.USER, udm_search_results[0]['dn'])
    #     udm_json = udm_res.json()
    #     self.assertEqual(udm_json['id'], 'Administrator')
    #     self.assertEqual(udm_search_results[0]['properties'], udm_json['properties'])
    #     udm_list_res = self.udm_client.list(UDMModel.USER, 'username', qfilter='(uid=Administrator)')
    #     self.assertEqual(len(udm_list_res), 1)
    #     self.assertIn('Administrator', udm_list_res)
    #     self.assertTrue(udm_list_res['Administrator'].dn.startswith('uid=Administrator,'))

    def test002_search_domain_administrators(self):
        udm_res = self.udm_client.request(
            UDMMethod.GET,
            UDMModel.GROUP,
            params=dict(
                filter="(cn=Domain Admins)",
            ),
        )
        udm_json = udm_res.json()
        self.assertEqual(udm_json["results"], 1)
        udm_search_results = udm_json["_embedded"]["udm:object"]
        self.assertEqual(len(udm_search_results), 1)
        self.assertEqual(udm_search_results[0]["id"], "Domain Admins")
        self.assertEqual(
            udm_search_results[0]["dn"],
            "cn=Domain Admins," + udm_search_results[0]["position"],
        )
        udm_list_res = self.udm_client.list(
            UDMModel.GROUP,
            "name",
            qfilter="(cn=Domain Admins)",
        )
        self.assertEqual(len(udm_list_res), 1)
        self.assertIn("Domain Admins", udm_list_res)
        self.assertTrue(
            udm_list_res["Domain Admins"].dn.startswith("cn=Domain Admins,"),
        )

    def test003_user_crud(self):
        # add new user
        rand_suffix = random_str(alphabet=string.ascii_lowercase, length=6)
        new_username = f"user-{rand_suffix}"
        new_email = f"Foo.Bar-{rand_suffix}@example.org"
        new_props = {
            "username": new_username,
            "description": "just an automated test",
            "firstname": "Foo",
            "lastname": "Bar",
            "displayName": "Bar",
            "e-mail": [new_email],
            "mailPrimaryAddress": new_email.lower(),
            "mailAlternativeAddress": [new_email.lower().replace("bar", "bar.alt")],
            "univentionObjectIdentifier": str(uuid.uuid1()),
            "password": gen_password(),
        }
        udm_res = self.udm_client.add(
            UDMModel.USER,
            new_props,
            position=self.user_position,
        )
        self.assertEqual(udm_res.status_code, HTTPStatus.CREATED)
        # search the new user
        udm_res = self.udm_client.user_query("username", new_username)
        udm_json = udm_res.json()
        new_dn = udm_json["_embedded"]["udm:object"][0]["dn"]
        self.assertTrue(new_dn.endswith(self.user_position))
        self.assertEqual(udm_json["results"], 1)
        self.assertEqual(udm_json["_embedded"]["udm:object"][0]["id"], new_username)
        for key, val in new_props.items():
            if key == "password":
                continue
            self.assertEqual(
                udm_json["_embedded"]["udm:object"][0]["properties"][key],
                val,
            )
        # modify user
        next_props = copy.deepcopy(new_props)
        next_props.update(
            {
                "description": "Now changed!",
            },
        )
        next_props.pop("password")
        udm_res = self.udm_client.modify(
            UDMModel.USER,
            new_dn,
            next_props,
        )
        self.assertEqual(udm_res.status_code, HTTPStatus.NO_CONTENT)
        # delete new user
        udm_res = self.udm_client.delete(
            UDMModel.USER,
            udm_json["_embedded"]["udm:object"][0]["dn"],
        )
        self.assertEqual(udm_res.status_code, HTTPStatus.NO_CONTENT)

    def test004_group_crud(self):
        # add new
        new_groupname = "group-" + random_str(alphabet=string.ascii_lowercase, length=5)
        udm_res = self.udm_client.add(
            UDMModel.GROUP,
            {
                "name": new_groupname,
                "description": "just an automated test",
                "users": [
                    f"uid=Administrator,cn=users,{self.udm_client.base_position}",
                ],
            },
            position=self.group_position,
        )
        # search the new group by name
        udm_res = self.udm_client.group_query("name", new_groupname)
        udm_json = udm_res.json()
        self.assertEqual(udm_json["results"], 1)
        self.assertEqual(udm_json["_embedded"]["udm:object"][0]["id"], new_groupname)
        group_props = udm_json["_embedded"]["udm:object"][0]["properties"]
        self.assertEqual(group_props["name"], new_groupname)
        self.assertEqual(group_props["description"], "just an automated test")
        self.assertEqual(
            group_props["users"],
            [f"uid=Administrator,cn=users,{self.udm_client.base_position}"],
        )
        # delete new group
        udm_res = self.udm_client.delete(
            UDMModel.GROUP,
            udm_json["_embedded"]["udm:object"][0]["dn"],
        )

    def test005_single_valued_props(self):
        self.udm_client.single_valued_props(UDMModel.USER)
        self.udm_client.single_valued_props(UDMModel.GROUP)

    def test006_ou_created(self):
        try:
            user_dn_comp = ldap.dn.str2dn(f"{CONNECTOR_CFG.udm.user_ou}")
            self.udm_client.query_dn_by_name(UDMModel.OU, user_dn_comp[0][0][1])

            group_dn_comp = ldap.dn.str2dn(f"{CONNECTOR_CFG.udm.group_ou}")
            self.udm_client.query_dn_by_name(UDMModel.OU, group_dn_comp[0][0][1])
        except KeyError:
            raise AssertionError(
                "User and group OU should be created if they does not exist",
            )


if __name__ == "__main__":
    unittest.main()
