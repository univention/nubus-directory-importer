# Directory Importer Performance Documentation

## Overview

This document provides setup instructions for testing the Directory Importer with various user counts. The tests were conducted to determine scalability limits and performance characteristics.

## Environment Setup

### Prerequisites

* An AD machine generated with https://jenkins2022.knut.univention.de/job/UCS-5.2/job/UCS-5.2-0/view/Personal%20environments/job/UcsW2k19ADEnvironment/ The AD connection details can be found in the UCS primary with `ucr dump | grep connector/ad`. You need to add the windows hostname to `/etc/hosts`.
* A Nubus for k8s deployment and it's UDM credentials.
  To run load tests with many users and groups, some configuration changes for large Nubus environments are necessary.
  If you deploy nubus with the helmfile configuration in the `ums-stack` repo, you can activate this configuration with: `--state-values-set toggles.loadTest=true`

  for more details see the [load test results documentation](./load-test-results_2025-02.md)

After you've provisioned the AD and UCS VM's,
shut both down and enable the `Always start VM with host`
flag in the UVMM UI.
This ensures that the VM's are excluded from the nightly test VM shutdown,
which would interrupt the load tests.

### Directory Connector host

You could start the directory connector on your laptop. For initial testing this is perfect.
But it has a couple major drawbacks for running a load test:
- The test performance will be scewed by your internet connection performance and the performance of the Univention VPN
- The load tests take a long time, often multiple days. You'll probably want to disconnect your laptop long before the load test is finished.

Instead you should use the UCS machine deployed by Jenkins alongside your AD VM.

To do that some pre-configuration is necessary:

#### Increase the VM memory

The Directory Importer is not particularly memory efficient.
It loads the complete source LDAP subtree into memory.
For this load test with 100k users this leads to about 10 GB of memory consumption
by the Directory Importer process.  
Each user came with a 100kB profile picture, thus
100k users * 0.1 MiB/user = 10 GiB

To prepare for this, you need to shut down the VM
and increase it's memory to 12 - 16 GB depending on how

#### Configure the UCS host

Install TMUX:

```sh
apt update && apt install -y tmux && tmux
```

Run the setup script: `./setup-directory-importer-host.sh`

Optionally configure the TMUX monitoring environment: `./configure-tmux.sh`

#### Run the Directory Importer

### Test Data Generation

```bash
PYTHONPATH=./tests python3 tests/load/ad_provisioner.py \
    --host ldap://10.207.118.192 \
    --admin-dn "cn=Administrator,cn=users,DC=ad,DC=test" \
    --password Univention.99 \
    --base-dn "DC=ad,DC=test" \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 10 \
    --group-with-max-users 1000 \
    --user-count 100 \
    --name-prefix 202501301544
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
   while true; do docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" directory-importer-directory-importer-1 | xargs -I {} echo "$(date '+%Y-%m-%d %H:%M:%S') {}" >> container_memory.log; sleep 1; done
   ```

## Debug performance bottlenecks

* Look at the CPU load of the pods:
`kubectl -n jlohmer-nubus-load-test top pods`
* Filter UDM REST API logs and get a feeling for the average request duration:
`kubectl -n jlohmer-nubus-load-test logs nubus-udm-rest-api-7cc947bfc7-nwxks --tail 1000 | rg ms`
* Filter LDAP logs and try to identify requests from UDM that take longer than they should:
`kubectl -n jlohmer-nubus-load-test logs nubus-ldap-server-primary-0 --tail 1000 --timestamps=true | rg conn=1570 | less`
