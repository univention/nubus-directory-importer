# LDAP directory synchronization with Univention Nubus

This component searches user and group entries via LDAP, e.g. in
MS Active Directory or OpenLDAP,  and syncs the users and groups found
via the UDM REST API to Nubus.

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
  * A service account has to be created in Nubus which allows to write
    users and groups in the configured target container (OU).

### Firewalling

  * The connector has to reach the target Nubus UDM REST API on port _443/tcp_.
  * The connector has to reach the source directory via TCP (e.g. port _636/tcp_).
  * No inbound connections are needed.

### Encrypted connections with TLS

Because this component sends clear-text passwords when connecting it is
required that all source and target systems are configured to properly
support encrypted connections via transport layer security (TLS).

See also: [BSI TR-02102 Kryptographische Verfahren: Empfehlungen und Schlüssellängen](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/Technische-Richtlinien/TR-nach-Thema-sortiert/tr02102/tr02102_node.html)

### Performance optimizations for large environments < 25,000 users

To synchronize a large number of users and groups to Nubus for Kubernetes
using the Nubus Directory Importer
in an acceptable time frame
some configuration changes are recommended:

#### Disable primary group updates.

Add the UCR variable `directory/manager/user/primarygroup/update: false` to the custom-values.yaml of your Nubus deployment:

```yaml
global:
  configUcr:
    directory:
      manager:
        user:
          primarygroup:
            update: false
```

Background:

By default, all synchronized users are added to the `Domain Users` group as their primary group in Nubus.
This group with a very large number of group members will eventually degrade user creation performance in an exponential way.
Our load tests showed significant performance degradation at 40000 group members / synchronized users.
This problem is specific to the size of a user's primary group.
See [this issue](https://git.knut.univention.de/univention/customers/dataport/team-souvap/-/issues/1016) for more details.

#### Index the `univentionObjectIdentifier' attribute in LDAP

**LDAP indexes can currently only be configured during initial deployment.**

Add `univentionObjectIdentifier` to the `ldap/index/eq` UCR variable.
**All existing indexes must be repeated.**

```yaml
    global:
      configUcr:
        directory:
          manager:
            user:
              primarygroup:
                update: false
        ldap:
          index:
            eq: aRecord,automountInformation,cNAMERecord,cn,description,dhcpHWAddress,displayName,entryUUID,gidNumber,givenName,homeDirectory,krb5PrincipalName,macAddress,mail,mailAlternativeAddress,mailPrimaryAddress,memberUid,objectClass,ou,pTRRecord,relativeDomainName,sambaAcctFlags,sambaDomainName,sambaGroupType,sambaPrimaryGroupSID,sambaSID,sambaSIDList,secretary,shadowExpire,sn,uid,uidNumber,uniqueMember,univentionCanonicalRecipientRewriteEnabled,univentionDataType,univentionInventoryNumber,univentionLicenseModule,univentionLicenseObject,univentionMailHomeServer,univentionNagiosHostname,univentionObjectFlag,univentionObjectType,univentionPolicyReference,univentionServerRole,univentionService,univentionShareGid,univentionShareSambaName,univentionShareWriteable,univentionUDMOptionModule,univentionUDMPropertyCLIName,univentionUDMPropertyCopyable,univentionUDMPropertyDefault,univentionUDMPropertyDeleteObjectClass,univentionUDMPropertyDoNotSearch,univentionUDMPropertyHook,univentionUDMPropertyLayoutOverwritePosition,univentionUDMPropertyLayoutOverwriteTab,univentionUDMPropertyLayoutPosition,univentionUDMPropertyLayoutTabAdvanced,univentionUDMPropertyLayoutTabName,univentionUDMPropertyLdapMapping,univentionUDMPropertyLongDescription,univentionUDMPropertyModule,univentionUDMPropertyMultivalue,univentionUDMPropertyObjectClass,univentionUDMPropertyOptions,univentionUDMPropertyShortDescription,univentionUDMPropertySyntax,univentionUDMPropertyTranslationLongDescription,univentionUDMPropertyTranslationShortDescription,univentionUDMPropertyTranslationTabName,univentionUDMPropertyValueMayChange,univentionUDMPropertyValueRequired,univentionUDMPropertyVersion,zoneName,univentionObjectIdentifier
```

Background:

`univentionObjectIdentifier` stores the primary ID of an object in the source directory.
UDM enforces the uniqueness of this attribute by searching for existing occurrences in LDAP.
This search eventually leads to exponential performance degradation if the attribute is not indexed.
Our load tests showed significant performance degradation between 50,000 and 60,000 synchronized users.
See [this comment](https://git.knut.univention.de/univention/customers/dataport/team-souvap/-/issues/1016#note_410827)

## Run it in docker compose

Copy the example configuration and customize it to fit your environment.
`cp ./config/ad-domain-config.yaml.example ./config/ad-domain-config.yaml`
Then start the Directory importer using docker compose in one of the following ways:

```shell
# Using the sub-command "up"
docker compose up

# Inspecting the CLI interface
docker compose run -it --rm directory-importer directory-importer --help

# Launching an interactive shell in the container
docker compose run -it --rm directory-importer bash
```

Note: The parameter `--build` can be added if you want to build the container
images from the local sources instead of fetching it from the registry.

### CLI interface and environment variables

The details of the CLI interface can be inspected with the following command:

```shell
docker compose run -it --rm directory-importer directory-importer --help
```

All arguments can also be influenced via environment variables. The environment
variables take precedence if set.

### TLS Support

You can use TLS to connect to AD and Nubus, for doing that you should mount the
`ca-certificates.crt` of those services in the respective place:
 - Nubus: `/etc/ssl/certs/ca-certificates-nubus.crt`
 - AD: `/etc/ssl/certs/ca-certificates-ad.crt`

After that, you have to uncomment the respective lines in the configuration file.

Also, you will have to adapt your `ad-domain-config.yaml` if you mount the certificates
in a different place.

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
    User's password used for authenticating to UDM.
    Can be also passed via environment variable `UDM_PASSWORD`.
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
    The Directory Importer considers itself the exclusive owner of this ou.
    It will delete all existing entries inside it that are not present in the source directory
  * user_primary_key_property: (optional)
    UDM property to use for storing the remote primary key for users.
  * user_properties: (optional)
    List of user property names the connector writes to.
  * group_ou: (mandatory)
    Name of the OU used as target container for group entries.
    The Directory Importer considers itself the exclusive owner of this ou.
    It will delete all existing entries inside it that are not present in the source directory
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
  * password: (mandatory)
    The clear-text password to use with LDAP simple bind operation.
    Can be also passed via environment variable `SOURCE_PASSWORD`.
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

The connector writes log messages at different log levels based on Python's
logging framework:

  * `DEBUG`
    Very detailed messages only used for development and debugging.
    Do not use in production.
  * `INFO`
    The normal log level used for production especially for logging
    all changes done to the target.
  * `WARN`
    Messages indicating something went wrong to be investigated at a later time.
  * `ERROR`
    Messages indicating something went wrong to be investigated immediately.

The following parameters are used to influence logging before the connector
reads its normal configuration file:

  * `LOG_LEVEL` / `--log-level`
    Minimum log level really written to logs (defaults to _INFO_)
  * `LOG_CONF` / `--log-conf`
    Full path name of a Python logging configuration file.
    If not set all log messages are simply written to _stderr_ with a
    format including a time-stamp.

See also:

  * [Python 3 docs -- logging: Configuration file format](https://docs.python.org/3/library/logging.config.html#logging-config-fileformat)

## Running repeatedly

The directory importer can be configured to repeat the synchronization with a
adjustable delay.

The following parameters are relevant for this mode:

  * `REPEAT=1` / `--repeat`
    Repeats the synchronization forever.
  * `REPEAT_DEPLAY` / `--repeat-delay`
    Allows to customize the delay after a synchronization run.

## Monitoring

The connector does not provide a monitoring end-point itself.

Some metrics could be extracted from log messages with tools like
_mtail_, _promtail_ or similar.

## Running tests

### Manual testing

Deploy the dependencies:
1. Deploy an Active Directory server
  https://jenkins2022.knut.univention.de/job/UCS-5.2/job/UCS-5.2-0/view/Personal%20environments/job/UcsW2k19ADEnvironment/
	The Joined UCS machine is redundant, but it's good enough until we figure out a better solution as part of the e2e test automation.
	This server is started inside the Univention VPN and thus the directory connector needs to also be started inside the VPN.
	Both Docker compose locall aswell as the gitlab pipelines fulfill this requirement.
2. Deploy Nubus for Kubernetes. Many possibilities, ums_stack pipeline, helmfile, helm... It needs to be reachable by the directory connector
	N4K does not need to be inside the VPN. The directory connector can also be configured to talk to a public or local IP.
3. Configure the Active Directory and UDM REST API connection and authorization parameters in the config.yaml file.

Executing the directory-importer inside a docker container using docker compose:
`docker compose up --build`

Alternatively run it locally:
Install shared objects for ldap python library to your system
- `uv sync -p /usr/bin/python3.10` (use system python to get shared objects)
- `uv run directory-importer config/ad-domain-config.yaml.example`

### Running the integration tests in docker compose

The integration tests require a UDM REST API and an openldap server
to act as the Nubus destination
and a local slapd and related slaptest infrastructure
to act as the source directory.
This environment can be automatically set up
with the `docker-compose-test.yaml` file.

To run them, just execute the following commands:

```bash
cd tests
# Start the test dependencies
docker compose down -v && docker compose up --pull always udm-rest-api ldap-server -d

# Create the example.org maildomain
./maildomain.sh

# Run the integration tests
docker compose run --build test pytest
```

### Running the integration tests locally (not recommended)

For running the tests you need:

  * Locally installed OpenLDAP server software (aka _slapd_)
  * python-ldap 3.4.0+
    (3.4.0 or newer because of recent changes in _slapdtest_ using
    _cn=config_ instead of _slapd.conf_)

You can directly execute the tests by invoking
[module unittest](https://docs.python.org/3/library/unittest.html)
from the command-line:

```
cd directory-importer/
python3 -m venv /path/to/venv
/path/to/venv/bin/pip install -e .
/path/to/venv/bin/python3 -W error -I -bb -m unittest
```

The command-line arguments `-W error -I -bb` are used to run the tests
in very strict mode (for details see
[Python 3 Command line -- Miscellaneous options](https://docs.python.org/3/using/cmdline.html#miscellaneous-options)).

You might have to set environment vars _BIN_ and _SBIN_ to indicate
where the OpenLDAP command-line tools and the _slapd_ executable can be found.

## Test cases

Note that modifying source entries and verifying the change in Nubus depends
on the actual configuration (attribute mapping/composition etc.). So this
section does not contain detailed attribute/property values.

### Users

#### Add user

Action in the source directory:

  * Add a new user not present in Nubus yet.

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

  * Add a new group not present in Nubus yet.

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
