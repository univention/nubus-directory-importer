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
