# Disclaimer - Work in progress

The repository you are looking into is work in progress.
It contains proof of concept and preview builds in development.

The repository's content provides you with first insights into the containerized cloud IAM from Univention, derived from the UCS appliance.

# LDAP directory synchronization with UCS

This component searches user and group entries via LDAP, e.g. in
MS Active Directory or OpenLDAP,  and syncs the users and groups found
via UDM REST API to UCS.

The synchronization always processes the full source data and thus does
not have to maintain any local state.

[[_TOC_]]

## Implementation notes

  * The connector always reads the full source and target data (users and groups)
    to calculate the required modifications in the target.
  * The connector does not store any local state.
  * Only a single source is configured. If you want to sync from multiple 
    sources simply run multiple instances with separate config files.
  * The OU structure of the AD source is ignored and all user and groups
    are written into a single dedicated target container (OU).
  * A configurable primary key is used to correctly synchronize renamed entries.
    Note that renaming a group which is referenced as nested group may require
    two connector runs to fully update the target entries.

## Prerequisites

### Access control

  * The source directory should have a dedicated service account configured
    which allows searching/reading all wanted users and groups entries.
  * A service account has to be created in UCS which allows to write
    users and groups in the configured target container (OU).

### Firewalling

  * The connector has to reach the target UCS system on port _443/tcp_.
  * The connector has to reach the source directory via TCP (e.g. port _636/tcp_).
  * No inbound connections are needed.

### Encrypted connections with TLS

Because this component sends clear-text passwords when connecting it is 
required that all source and target systems are configured to properly 
support encrypted connections via transport layer security (TLS).

See also: [BSI TR-02102 Kryptographische Verfahren: Empfehlungen und Schlüssellängen](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/Technische-Richtlinien/TR-nach-Thema-sortiert/tr02102/tr02102_node.html)

## Installation

### Dependencies

  * _setuptools_
  * [certifi](https://certifiio.readthedocs.io)
  * [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers)
  * [python-ldap](python-ldap.org)
  * [requests](https://docs.python-requests.org)
  * [strictyaml](https://hitchdev.com/strictyaml/)
  * [junkaptor](https://code.stroeder.com/pymod/python-junkaptor)

### Install with pip

Install with _pip_ into virtual environment directory `/opt/udm-directory-connector`:

```
tar xzf udm-directory-connector-0.0.1.tar.gz
cd udm-directory-connector-0.0.1
python3 -m venv /opt/udm-directory-connector
/opt/udm-directory-connector/bin/pip install .
mkdir /etc/udm-directory-connector
```

### Create Debian package

You can use the _setuptools_ helper module [stdeb](https://pypi.org/project/stdeb/)
to generate Debian/Ubuntu packages.
The file _stdeb.cfg_ is provided to faciliate use of this.

See also [container-stdeb](https://code.stroeder.com/pymod/container-stdeb)
for running the package builds in a separate container.

## Usage

Note that _udm-directory-connector_ process has to be invoked in regular
time-intervals either as a CRON job or triggered by a
[systemd.timer](https://www.freedesktop.org/software/systemd/man/systemd.timer.html).

### From within a virtual env

If installed into virtual environment `/opt/udm-directory-connector`
you can invoke the auto-generate wrapper script:

```
/opt/udm-directory-connector/bin/udm-directory-connector /etc/udm-directory-connector/config-ad.example.com.yml
```

To provide stricter run-time settings with
[Python's command-line arguments](https://docs.python.org/3/using/cmdline.html#command-line):

```
/opt/udm-directory-connector/bin/python3 -W error -I -bb -m udm_directory_connector /etc/udm-directory-connector/config-ad.example.com.yml
```

### Packaged executable

If installed from Debian/Ubuntu package:

```
/usr/bin/udm-directory-connector /etc/udm-directory-connector/config-ad.example.com.yml
```

### With systemd service units

See example systemd service unit for a so-called one-shot service: 
[udm-directory-connector@.service](systemd/udm-directory-connector@.service)

For running multiple synchronization processes on a single system
use systemd service instances and use
[specifiers](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Specifiers)
referencing separate config files.

For each sync process create a systemd timer unit triggering a service unit instance.
See example systemd timer unit for triggering the one-short service: 
[udm-directory-connector.service](systemd/udm-directory-connector.timer)

See relevant systemd man-pages:

  * [systemd.unit(5) - Specifiers](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Specifiers)
  * [systemd.exec(5)](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)
  * [systemd.exec(5) - Sandboxing](https://www.freedesktop.org/software/systemd/man/systemd.exec.html#Sandboxing)
  * [systemd.timer(5)](https://www.freedesktop.org/software/systemd/man/systemd.timer.html)

## Configuration

The configuration file is written in YAML syntax and is structured as a hierarchy.

See configuration example in source distribution directory [config/](config/).

At the top hierarchy level there are these config dictionaries:

  * udm: 
    Parameters for configuring how to reach UDM and some more.
  * source: 
    Parameters for configuring how to connect to the LDAP source directory 
    and some data transformation rules.

### udm:

  * uri: (mandatory) 
    URI including base path for accessing UDM REST API
  * user: (mandatory) 
    User's name used for authenticating to UDM
  * password: (mandatory) 
    User's password used for authenticating to UDM
  * ca_cert: (optional) 
    Path name of the trusted CA certificate bundle file. 
    Defaults to your platform-specific CA bundle file.
  * skip_writes: (optional)
    If `true` this skips write operations to UDM (default `false`).
  * connect_timeout: (optional) 
    Timeout in seconds to wait for connection to UDM (default 6.0 secs).
  * read_timeout: (optional) 
    Timeout in seconds to wait for UDM results (default 1800 secs).
  * user_ou: (mandatory) 
    Name of the OU used as target container for user entries.
  * user_primary_key_property: (optional) 
    UDM property to use for storing the remote primary key for users.
  * user_properties: (optional)
    List of user property names the connector writes to.
  * group_ou: (mandatory) 
    Name of the OU used as target container for group entries.
  * group_primary_key_property: (optional) 
    UDM property to use for storing the remote primary key for groups.
  * group_properties: (optional)
    List of group property names the connector writes to.

### source:

  * ldap_uri: (mandatory) 
    LDAP URI of the source directory to connect to. 
    Ideally you should configure an URI starting with `ldaps://` here to 
    ensure LDAP over TLS is used right from the beginning. 
    Note that the OpenLDAP client library (libldap) used by python-ldap
    implements a TLS hostname check strictly requring the hostname in
    the LDAP URI to match one of the DNS values of X.509v3 extension
    _subjectAltName_ in the source directory's TLS server certificate.
  * bind_dn: (mandatory) 
    The bind DN to use authenticate to the source directory via LDAP simple bind operation.
  * bind_pw: (mandatory) 
    The clear-text password to use with LDAP simple bind operation.
  * ca_cert: (optional) 
    Path name of the trusted CA certificate bundle file. 
    Defaults to your platform-specific CA bundle file.
  * timeout: (optional) 
    Timeout in seconds to wait for network (default 5 secs).
  * search_pagesize: (optional) 
    Page size to used when searching with _Simple Paged Results_ control.
  * user_base: (mandatory) 
    search base used when searching user entries.
  * user_scope: "sub" 
    Search scope used when searching user entries.
    ("one" or "sub", default "sub").
  * user_filter: (optional) 
    LDAP filter used when searching user entries.
  * user_attrs: (optional) 
    LDAP attributes to be requested while searching for users.
    Recommendation is to only list the attributes actually used in
    transformation/mapping later.
  * user_range_attrs: (optional) 
    LDAP user attributes for which values are optionally retrieved by
    _Range Retrieval_ (for MS AD)
  * user_trans: 
    Data transformation configuration applied to user entries.
  * group_base: (mandatory) 
    search base used when searching group entries.
  * group_scope: "sub" 
    Search scope used when searching group entries.
    ("one" or "sub", default "sub").
  * group_filter: (optional) 
    LDAP filter used when searching group entries.
  * group_attrs: (optional) 
    LDAP attributes to be requested while searching for groups.
    Recommendation is to only list the attributes actually used in
    transformation/mapping later.
  * group_range_attrs: (optional) 
    LDAP group attributes for which values are optionally retrieved by
    _Range Retrieval_ (for MS AD)
  * group_trans: 
    Data transformation configuration applied to group entries.

## Logging

The connector writes log messages at different log level:

  * DEBUG 
    Very detailed messages only used for development and debugging.
    Do not use in production.
  * INFO 
    The normal log level used for production especially for logging
    all changes done to the target.
  * WARN 
    Messages indicating something went wrong to be investigated at a later time.
  * ERROR 
    Messages indicating something went wrong to be investigated immediately.

The following environment variables are used to influence logging before
the connector reads its normal configuration file:

  * LOG_LEVEL 
    Minimum log level really written to logs (defaults to _INFO_)
  * LOG_CONF 
    Full path name of a Python logging configuration file.
    If not set all log messages are simply written to _stderr_ with a
    format including a time-stamp.

See also:

  * [Python 3 docs -- logging: Configuration file format](https://docs.python.org/3/library/logging.config.html?highlight=logging#logging-config-fileformat)

## Monitoring

The connector does not provide a monitoring end-point itself.

Some metrics could be extracted from log messages with tools like
_mtail_, _promtail_ or similar.

## Running tests

### Running the tests in docker compose

The integration tests require a UDM REST API and an openldap server
to act as the Nubus destination
and a local slapd and related slaptest infrastructure
to act as the source directory.
This environment can be automatically set up
with the `docker-compose-test.yaml` file.

To run them, just execute the following commands:

```bash
# Start the test dependencies
docker compose down -v && docker compose up --pull always udm-rest-api ldap-server

./maildomain.sh

# Run the integration tests
docker compose run --build test .venv/bin/python3 -m pytest
```

### Running the tests locally (not recommended)

For running the tests you need:

  * Locally installed OpenLDAP server software (aka _slapd_)
  * python-ldap 3.4.0+
    (3.4.0 or newer because of recent changes in _slapdtest_ using
    _cn=config_ instead of _slapd.conf_)

You can directly execute the tests by invoking
[module unittest](https://docs.python.org/3/library/unittest.html)
from the command-line:

```
cd udm-directory-connector/
python3 -m venv /path/to/venv
/path/to/venv/bin/pip install -e .
/path/to/venv/bin/python3 -W error -I -bb -m unittest
```

The command-line arguments `-W error -I -bb` are used to run the tests
in very strict mode (for details see
[Python 3 Command line -- Miscellaneous options](https://docs.python.org/3/using/cmdline.html#miscellaneous-options)).

You might have to set environment vars _BIN_ and _SBIN_ to indicate
where the OpenLDAP command-line tools and the _slapd_ executable can be found.

It is highly recommended to run the tests in a virtual env
dynamically created by [tox](https://tox.wiki/en/latest/):

```
BIN=/opt/openldap-ms/bin:/opt/openldap-ms/sbin SBIN=/opt/openldap-ms/sbin tox
```

## Test cases

Note that modifying source entries and verifying the change in UCS depends
on the actual configuration (attribute mapping/composition etc.). So this
section does not contain detailed attribute/property values.

### Users

#### Add user

Action in the source directory:

  * Add a new user not present in UCS yet.

Expected result:

  * New user was added after next connector run.
  * Attribute value _uid_ matches configured user name
    in the source directory.
  * Attribute value _univentionObjectIdentifier_ matches the configured
    primary attribute value in the source directory.

#### Modify user

Action in the source directory:

  * Modify some attributes in the source directory
    which are mapped to UDM properties in the configuration,
    e.g. mail, description, but not(!) the username (uid or sAMAccountName).

Expected result:

  * Existing user was modified after next connector run.

#### Rename user

Action in the source directory:

  * Modify username attributes in the source directory,
    e.g. uid or sAMAccountName.

Expected result:

  * Existing user was renamed after next connector run.
  * Attribute value _uid_ matches configured username
    in the source directory.
  * User is still member of the same groups.

#### Delete user

Action in the source directory:

  * Delete a user entry in the source directory.

Expected result:

  * Existing user was removed after next connector run.

### Groups

#### Add group

Action in the source directory:

  * Add a new group not present in UCS yet.

Expected result:

  * New group was added after next connector run.
  * Attribute value _cn_ matches configured group name
    in the source directory.
  * Attribute value _univentionObjectIdentifier_ matches the configured
    primary attribute value in the source directory.

#### Modify group

Action in the source directory:

  * Modify some attributes in the source directory
    which are mapped to UDM properties in the configuration,
    e.g. _description_.

Expected result:

  * Existing group was modified after next connector run.

#### Add user to group

#### Remove user from group

#### Rename group

Action in the source directory:

  * Modify group name attributes in the source directory,
    e.g. _cn_.

Expected result:

  * Existing group was renamed after next connector run.
  * Attribute value _cn_ matches configured group name
    in the source directory.

#### Delete group

Action in the source directory:

  * Delete a group entry in the source directory.

Expected result:

  * Existing group was removed after next connector run.
