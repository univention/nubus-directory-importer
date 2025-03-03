# directory-importer

The Nubus Directory Importer provides a daemon
that can synchronize users from a source Directory to a Nubus deployment.
An example source directory is an Active Directory LDAP

More documentation can be found at:
https://docs.software-univention.de/nubus-kubernetes-operation/latest/en/howto-connect-external-iam.html#howto-connect-external-iam-setup

- **Version**: 1.0.1
- **Type**: application
- **AppVersion**:
-

## Introduction

This chart does install the Guardian Authorization API.

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| oci://artifacts.software-univention.de/nubus/charts | nubus-common | ^0.8.x |

## Values

<table>
	<thead>
		<th>Key</th>
		<th>Type</th>
		<th>Default</th>
		<th>Description</th>
	</thead>
	<tbody>
		<tr>
			<td>config.logLevel</td>
			<td>string</td>
			<td><pre lang="json">
"INFO"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>config.loggingConfig</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>config.repeat</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>config.repeatDelay</td>
			<td>int</td>
			<td><pre lang="json">
300
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.bind_dn</td>
			<td>string</td>
			<td><pre lang="json">
"CN=readonly-ad-machine-user,CN=Users,DC=ad,DC=test"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_base</td>
			<td>string</td>
			<td><pre lang="json">
"CN=Groups,DC=ad,DC=test"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_scope</td>
			<td>string</td>
			<td><pre lang="json">
"sub"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_trans.remove_attrs[0]</td>
			<td>string</td>
			<td><pre lang="json">
"objectGUID"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_trans.remove_attrs[1]</td>
			<td>string</td>
			<td><pre lang="json">
"objectSid"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_trans.rename_attrs.name</td>
			<td>string</td>
			<td><pre lang="json">
"cn"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_trans.rename_attrs.univentionObjectIdentifier</td>
			<td>string</td>
			<td><pre lang="json">
"objectGUID"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.group_trans.rename_attrs.users</td>
			<td>string</td>
			<td><pre lang="json">
"member"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.ldap_uri</td>
			<td>string</td>
			<td><pre lang="json">
"ldap://my_active_directory_server.test:1234"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.password</td>
			<td>string</td>
			<td><pre lang="json">
"supersecret"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.search_pagesize</td>
			<td>int</td>
			<td><pre lang="json">
500
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.timeout</td>
			<td>int</td>
			<td><pre lang="json">
5
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[0]</td>
			<td>string</td>
			<td><pre lang="json">
"objectGUID"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[10]</td>
			<td>string</td>
			<td><pre lang="json">
"st"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[11]</td>
			<td>string</td>
			<td><pre lang="json">
"c"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[12]</td>
			<td>string</td>
			<td><pre lang="json">
"telephoneNumber"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[13]</td>
			<td>string</td>
			<td><pre lang="json">
"mobile"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[14]</td>
			<td>string</td>
			<td><pre lang="json">
"employeeNumber"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[15]</td>
			<td>string</td>
			<td><pre lang="json">
"employeeType"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[16]</td>
			<td>string</td>
			<td><pre lang="json">
"proxyAddresses"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[1]</td>
			<td>string</td>
			<td><pre lang="json">
"sAMAccountName"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[2]</td>
			<td>string</td>
			<td><pre lang="json">
"givenName"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[3]</td>
			<td>string</td>
			<td><pre lang="json">
"description"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[4]</td>
			<td>string</td>
			<td><pre lang="json">
"sn"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[5]</td>
			<td>string</td>
			<td><pre lang="json">
"ou"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[6]</td>
			<td>string</td>
			<td><pre lang="json">
"o"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[7]</td>
			<td>string</td>
			<td><pre lang="json">
"street"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[8]</td>
			<td>string</td>
			<td><pre lang="json">
"l"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_attrs[9]</td>
			<td>string</td>
			<td><pre lang="json">
"postalCode"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_base</td>
			<td>string</td>
			<td><pre lang="json">
"CN=Users,DC=ad,DC=test"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_filter</td>
			<td>string</td>
			<td><pre lang="json">
"(\u0026(objectClass=user)(sAMAccountType=805306368)(givenName=*)(sn=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_scope</td>
			<td>string</td>
			<td><pre lang="json">
"sub"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.decompose_attrs.proxyAddresses[0]</td>
			<td>string</td>
			<td><pre lang="json">
"^SMTP:(?P\u003cmail\u003e.+)$"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.decompose_attrs.proxyAddresses[1]</td>
			<td>string</td>
			<td><pre lang="json">
"^smtp:(?P\u003cmailAlternativeAddress\u003e.+)$"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_attrs[0]</td>
			<td>string</td>
			<td><pre lang="json">
"objectGUID"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_attrs[1]</td>
			<td>string</td>
			<td><pre lang="json">
"objectSid"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_attrs[2]</td>
			<td>string</td>
			<td><pre lang="json">
"proxyAddresses"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_values.telephoneNumber[0]</td>
			<td>string</td>
			<td><pre lang="json">
"+49"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_values.telephoneNumber[1]</td>
			<td>string</td>
			<td><pre lang="json">
"+49 ???"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.remove_values.telephoneNumber[2]</td>
			<td>string</td>
			<td><pre lang="json">
"0"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.city</td>
			<td>string</td>
			<td><pre lang="json">
"l"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.country</td>
			<td>string</td>
			<td><pre lang="json">
"c"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.e-mail</td>
			<td>string</td>
			<td><pre lang="json">
"mail"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.firstname</td>
			<td>string</td>
			<td><pre lang="json">
"givenName"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.lastname</td>
			<td>string</td>
			<td><pre lang="json">
"sn"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.mobileTelephoneNumber</td>
			<td>string</td>
			<td><pre lang="json">
"mobile"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.organisation</td>
			<td>string</td>
			<td><pre lang="json">
"o"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.phone</td>
			<td>string</td>
			<td><pre lang="json">
"telephoneNumber"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.postcode</td>
			<td>string</td>
			<td><pre lang="json">
"postalCode"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.univentionObjectIdentifier</td>
			<td>string</td>
			<td><pre lang="json">
"objectGUID"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.rename_attrs.username</td>
			<td>string</td>
			<td><pre lang="json">
"sAMAccountName"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.replace_values.c."Bundesrepublik Deutschland"</td>
			<td>string</td>
			<td><pre lang="json">
"DE"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.replace_values.c.Deutschland</td>
			<td>string</td>
			<td><pre lang="json">
"DE"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.replace_values.c.Frankreich</td>
			<td>string</td>
			<td><pre lang="json">
"FR"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.facsimileTelephoneNumber[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.fax[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.homePhone[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.homeTelephoneNumber[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailAlternativeAddress[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:mail_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailAlternativeAddress[1]</td>
			<td>string</td>
			<td><pre lang="json">
"bytes.lower"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailLocalAddress[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:mail_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailLocalAddress[1]</td>
			<td>string</td>
			<td><pre lang="json">
"bytes.lower"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailPrimaryAddress[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:mail_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mailPrimaryAddress[1]</td>
			<td>string</td>
			<td><pre lang="json">
"bytes.lower"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mail[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:mail_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mail[1]</td>
			<td>string</td>
			<td><pre lang="json">
"bytes.lower"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mobileTelephoneNumber[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.mobile[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.objectGUID[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:guid2uuid"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.source.user_trans.sanitizer.telephoneNumber[0]</td>
			<td>string</td>
			<td><pre lang="json">
"univention.directory_importer.sanitize:phone_sanitizer"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.group_ou</td>
			<td>string</td>
			<td><pre lang="json">
"ou=ad-domain-example"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.group_primary_key_property</td>
			<td>string</td>
			<td><pre lang="json">
"univentionObjectIdentifier"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.password</td>
			<td>string</td>
			<td><pre lang="json">
"supersecret"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.skip_writes</td>
			<td>bool</td>
			<td><pre lang="json">
false
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.uri</td>
			<td>string</td>
			<td><pre lang="json">
"https://nubus-kubernetes-deployment.test/univention/udm/"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.user</td>
			<td>string</td>
			<td><pre lang="json">
"Administrator"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.user_ou</td>
			<td>string</td>
			<td><pre lang="json">
"ou=ad-domain-example"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>configFile.udm.user_primary_key_property</td>
			<td>string</td>
			<td><pre lang="json">
"univentionObjectIdentifier"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>extraEnvVars</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>Array with extra environment variables to add to containers.  extraEnvVars:   - name: FOO     value: "bar"</td>
		</tr>
		<tr>
			<td>extraSecrets</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>Optionally specify a secret to create (primarily intended to be used in development environments to provide custom certificates)</td>
		</tr>
		<tr>
			<td>extraVolumeMounts</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>Optionally specify an extra list of additional volumeMounts.</td>
		</tr>
		<tr>
			<td>extraVolumes</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>Optionally specify an extra list of additional volumes.</td>
		</tr>
		<tr>
			<td>global.imagePullPolicy</td>
			<td>string</td>
			<td><pre lang="json">
"IfNotPresent"
</pre>
</td>
			<td>Define an ImagePullPolicy.  Ref.: https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy </td>
		</tr>
		<tr>
			<td>global.imagePullSecrets</td>
			<td>list</td>
			<td><pre lang="json">
[]
</pre>
</td>
			<td>Credentials to fetch images from private registry. Ref: https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/  imagePullSecrets:   - "docker-registry"</td>
		</tr>
		<tr>
			<td>global.imageRegistry</td>
			<td>string</td>
			<td><pre lang="json">
"artifacts.software-univention.de"
</pre>
</td>
			<td>Container registry address.</td>
		</tr>
		<tr>
			<td>image</td>
			<td>object</td>
			<td><pre lang="json">
{
  "imagePullPolicy": "",
  "registry": "",
  "repository": "nubus/images/directory-importer",
  "sha256": null,
  "tag": "latest"
}
</pre>
</td>
			<td>Container image configuration</td>
		</tr>
		<tr>
			<td>image.sha256</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td>Define image sha256 as an alternative to `tag`</td>
		</tr>
		<tr>
			<td>probes.liveness.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.liveness.failureThreshold</td>
			<td>int</td>
			<td><pre lang="json">
3
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.liveness.initialDelaySeconds</td>
			<td>int</td>
			<td><pre lang="json">
120
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.liveness.periodSeconds</td>
			<td>int</td>
			<td><pre lang="json">
30
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.liveness.successThreshold</td>
			<td>int</td>
			<td><pre lang="json">
1
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.liveness.timeoutSeconds</td>
			<td>int</td>
			<td><pre lang="json">
3
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.enabled</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.failureThreshold</td>
			<td>int</td>
			<td><pre lang="json">
30
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.initialDelaySeconds</td>
			<td>int</td>
			<td><pre lang="json">
30
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.periodSeconds</td>
			<td>int</td>
			<td><pre lang="json">
15
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.successThreshold</td>
			<td>int</td>
			<td><pre lang="json">
1
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>probes.readiness.timeoutSeconds</td>
			<td>int</td>
			<td><pre lang="json">
3
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>resources.limits.cpu</td>
			<td>string</td>
			<td><pre lang="json">
"4"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>resources.limits.memory</td>
			<td>string</td>
			<td><pre lang="json">
"4Gi"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>resources.requests.cpu</td>
			<td>string</td>
			<td><pre lang="json">
"250m"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>resources.requests.memory</td>
			<td>string</td>
			<td><pre lang="json">
"512Mi"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.allowPrivilegeEscalation</td>
			<td>bool</td>
			<td><pre lang="json">
false
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.capabilities.drop[0]</td>
			<td>string</td>
			<td><pre lang="json">
"ALL"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.privileged</td>
			<td>bool</td>
			<td><pre lang="json">
false
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.readOnlyRootFilesystem</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.runAsGroup</td>
			<td>int</td>
			<td><pre lang="json">
1000
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.runAsNonRoot</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.runAsUser</td>
			<td>int</td>
			<td><pre lang="json">
1000
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>securityContext.seccompProfile.type</td>
			<td>string</td>
			<td><pre lang="json">
"RuntimeDefault"
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>serviceAccount.annotations</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>serviceAccount.automountServiceAccountToken</td>
			<td>bool</td>
			<td><pre lang="json">
false
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>serviceAccount.create</td>
			<td>bool</td>
			<td><pre lang="json">
true
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>serviceAccount.labels</td>
			<td>object</td>
			<td><pre lang="json">
{}
</pre>
</td>
			<td>Additional custom labels for the ServiceAccount.</td>
		</tr>
		<tr>
			<td>serviceAccount.name</td>
			<td>string</td>
			<td><pre lang="json">
""
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>sourceDirectory.auth.existingSecret.keyMapping.password</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>sourceDirectory.auth.existingSecret.name</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>sourceDirectory.auth.password</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>udm.auth.existingSecret.keyMapping.password</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>udm.auth.existingSecret.name</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
		<tr>
			<td>udm.auth.password</td>
			<td>string</td>
			<td><pre lang="json">
null
</pre>
</td>
			<td></td>
		</tr>
	</tbody>
</table>

