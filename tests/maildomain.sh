#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

curl -X POST "http://localhost:9979/udm/mail/domain/" \
     -u "cn=admin:univention" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
           "properties": {
             "name": "example.org",
             "objectFlag": []
           },
           "position": "cn=domain,cn=mail,dc=univention-organization,dc=intranet"
         }'
           # "uri": "http://localhost:9979/udm/mail/domain/cn=example.org,cn=domain,cn=mail,dc=univention-organization,dc=intranet"
