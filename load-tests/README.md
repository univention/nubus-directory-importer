# Directory Importer Performance Documentation

## Overview

This document provides setup instructions for testing the Directory Importer with various user counts. The tests were conducted to determine scalability limits and performance characteristics.

## Environment Setup

### Prerequisites

* An AD machine generated with https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-9/view/Personal%20environments/job/UcsW2k19ADEnvironment/ The AD connection details can be found in the UCS primary with `ucr dump | grep connector/ad`. You need to add the windows hostename to `/etc/hosts`.
* A Nubus for k8s deployment and it's UDM credentials.


### Test Data Generation

```bash
python ad_provisioner.py \
    --host ldap://your-ad-server \
    --admin-dn "cn=Administrator,cn=users,DC=ad,DC=test" \
    --password "password" \
    --base-dn "DC=ad,DC=test" \
    --user-count 1000 \
    --users-per-group 100
```

### Directory Importer Configuration

1. Copy the sample configuration:
  ```bash
  cp ad-domain-config-load-tests.yaml.example ../config/ad-domain-config.yaml
  ```
1. Update the configuration with your environment details:

## Running the Tests

1. Start the Directory Importer:
  ```bash
  docker compose up --build
  ```
1. Monitor the process:
  ```bash
   while true; do docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" directory-importer-udm-directory-connector-1 | xargs -I {} echo "$(date '+%Y-%m-%d %H:%M:%S') {}" >> container_memory.log; sleep 1; done
   ```
