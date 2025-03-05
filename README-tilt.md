# Directory Importer Tilt dev-env

In this directory is a simple tilt-based dev-env
to help develop the directory importer helm chart and container image.

## Dependencies

### Source LDAP

The directory importer requires a source LDAP server.
How to start this is explained in the [E2E test docs](../tests/e2e/README.md)

You then need to configure the LDAP connection parameters
of the source directory in the `./tilt-values.yaml`

### UDM REST API

In addition it requires a Nubus LDAP Server and UDM REST API.
The easiest and preconfigured way is to start the two
is using Tilt in the `dev-env` repo:
```sh
TILT_PORT=10351 tilt up keycloak ldap-server udm-rest-api stack-data-ums
```

If you don't want to use the dev-env repo, you can use any other Nubus deployment
with a running and accessible UDM REST API.
You just need to change the config in the 

## Run

Then you can start the Tiltfile in this repo
and enjoy automatic redeployments for every change

```sh
tilt up
```
