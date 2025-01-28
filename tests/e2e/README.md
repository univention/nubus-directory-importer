# E2E Tests

This directory contains end-to-end tests for the project.

## Active Directory

The tests require an Active Directory to run. There is a VM in the KVM host
[`skurup`](skurup.knut.univention.de). The VM is called `nubus_W2k19AD_directory_importer`
and is accessible from [UVMM](https://uvmm.knut.univention.de/). The VM has a
snapshot called `base`, which is the one that should be used for the tests.

## Running the tests

To run the tests, you need to add the following entry to your `/etc/hosts` file:

```
10.207.116.197 WIN-N8V5GD1V1L.ad.test
```

Then, you need to create the file `tests/e2e/importer-config.yaml` with the
content from the CI/CD variable `$E2E_DIRECTORY_IMPORTER_CONFIG`.
