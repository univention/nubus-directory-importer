#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
Create a UDM extended attribute for the deprovision timestamp.

Reads config from ad-domain-config.yaml; the extended attribute name
is taken from udm.deprovision_timestamp_property.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import certifi
import requests
import yaml


def delete_extended_attribute(
    udm_uri: str,
    udm_user: str,
    udm_password: str,
    ea_name: str,
    ldap_base: str,
    ca_cert: Optional[str] = None,
) -> None:
    """Delete an existing extended attribute by name."""

    if udm_uri.endswith("/"):
        udm_uri = udm_uri.rstrip("/")

    url = f"{udm_uri}/settings/extended_attribute/"
    auth = (udm_user, udm_password)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    params = {"query[name]": ea_name}

    print(f"GET {url}?query[name]={ea_name}")
    resp = requests.get(url, auth=auth, headers=headers, params=params, verify=ca_cert or certifi.where())
    resp.raise_for_status()

    results = resp.json()
    if results["results"] == 0:
        print(f"Extended attribute {ea_name} does not exist, nothing to delete")
        return

    udm_objects = results["_embedded"]["udm:object"]
    for obj in udm_objects:
        obj_dn = obj["dn"]
        delete_url = f"{udm_uri}/settings/extended_attribute/{obj_dn}"
        print(f"DELETE {delete_url}")
        del_resp = requests.delete(delete_url, auth=auth, headers=headers, verify=ca_cert or certifi.where())
        del_resp.raise_for_status()
        print(f"Deleted {ea_name} at {obj_dn}")


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load and return the full YAML configuration."""
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def create_deprovision_ea(
    udm_uri: str,
    udm_user: str,
    udm_password: str,
    deprovision_timestamp_property: str,
    ldap_base: str,
    ca_cert: Optional[str] = None,
) -> None:
    """Create the deprovision timestamp extended attribute."""

    if udm_uri.endswith("/"):
        udm_uri = udm_uri.rstrip("/")

    url = f"{udm_uri}/settings/extended_attribute/"
    auth = (udm_user, udm_password)

    position = f"cn=custom attributes,cn=univention,{ldap_base}"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    name = deprovision_timestamp_property
    short_desc = f"Directory Importer {deprovision_timestamp_property}"
    long_desc = "Timestamp when the user was deprovisioned by the directory importer"

    props: Dict[str, Any] = {
        "name": name,
        "shortDescription": short_desc,
        "longDescription": long_desc,
        "module": ["users/user"],
        "syntax": "string",
        "multivalue": False,
        "valueRequired": False,
        "mayChange": True,
        "doNotSearch": True,
        "objectClass": "univentionFreeAttributes",
        "ldapMapping": "univentionFreeAttribute11",
    }

    payload = {
        "position": position,
        "properties": props,
    }

    print(f"POST {url}")
    resp = requests.post(
        url,
        json=payload,
        auth=auth,
        headers=headers,
        verify=ca_cert or certifi.where(),
    )
    if not resp.ok:
        print(f"Error {resp.status_code}: {resp.reason}", file=sys.stderr)
        print(f"Response body: {resp.text}", file=sys.stderr)
        sys.exit(1)
    result = resp.json()
    print(f"Created: {result.get('dn', result)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a UDM extended attribute for the deprovision timestamp.",
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base LDAP DN, e.g. DC=ad,DC=test",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the extended attribute before creating it",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the extended attribute and exit",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    udm = cfg["udm"]

    ea_name = udm["deprovision_timestamp_property"]
    if args.force or args.delete:
        delete_extended_attribute(
            udm_uri=udm["uri"],
            udm_user=udm["user"],
            udm_password=udm["password"],
            ea_name=ea_name,
            ldap_base=args.base,
            ca_cert=udm.get("ca_cert"),
        )
        if args.delete:
            return

    create_deprovision_ea(
        udm_uri=udm["uri"],
        udm_user=udm["user"],
        udm_password=udm["password"],
        deprovision_timestamp_property=ea_name,
        ldap_base=args.base,
        ca_cert=udm.get("ca_cert"),
    )


if __name__ == "__main__":
    main()
