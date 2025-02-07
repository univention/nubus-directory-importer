# Directory importer load-tests

Synchronization performance of the Directory Importer
when using it to import users and groups from AD to Nubus for Kubernetes.

## Summary

For an environment with 40k users and 40k groups:

The initial sync takes between:
17.50 hours (0 days 17:30:14) and
32.30 hours (1 day 08:17:46)

A resync with no actual changes takes on average:
275 seconds (4:35 minutes)

The memory consumption mostly depends on the size of the source LDAP subtree.
For 40k users, it was hovering between 4GB and 5GB.

Average sync rate per user is between
1.2201 seconds and 1.3740 seconds

Average sync rate per group is between
0.3506 seconds and 6.0207

User sync rate was very stable and probably bottlenecked by the UDM REST API.
If it becomes exponentially worse, it's an indication that Nubus
is not correctly configured / tuned for the directory size.
See [Nubus configuration changes](###Nubus configuration changes)

Group sync rate depends on the group size
and is mostly bottlenecked by LDAP disk write IO.

### Nubus configuration changes

A few configuration changes were necessary to complete the above mentioned load tests.
These values are not perfectly tuned, but instead set to very large values
to not interfere with the load test.

`load-test-values.yaml`:
``` yaml
global:
  configUcr:
    directory:
      manager:
        user:
          primarygroup:
            # required: Disable primary group updates when creating users.
            # If this option is disabled, every user is added to the same default primary group. (Domain Users)
            # This will cause performance degregation when the group gets extremely large.
            update: false
        rest:
          # Increase the internal request timeout in the UDM REST API
          response-timeout: 3600

nubusUdmRestApi:
  # Increase resource limits for the UDM REST API
  resources:
    limits:
      cpu: 5000
      memory: "20Gi"
  # Icrease the ingress controllers (nginx) request timeouts for the UDM REST API's routes
  ingress:
    annotations:
      nginx.ingress.kubernetes.io/proxy-connect-timeout: "360"
      nginx.ingress.kubernetes.io/proxy-send-timeout: "360"
      nginx.ingress.kubernetes.io/proxy-read-timeout: "360"

nubusLdapServer:
  # Increase resource limits for the LDAP primaries
  resourcesPrimary:
    limits:
      cpu: 5000
      memory: "20Gi"
  # Increase resource limits for the LDAP secondaries
  resourcesSecondary:
    limits:
      cpu: 5000
      memory: "20Gi"
  # optional: Configure the LDAP servers persistent volumes to write to kubernetes-nodes local storage
  # instead of a cluster filesystem like Ceph. (The default in the Gaia cluster)
  # May increase LDAP write performance.
  persistence:
    storageClass: "local-storage"
```

### Configuration for even bigger environments (100k)
Larger environments probably require configuring an additional LDAP index.
Configure the UCR Variable: `ldap/index/eq=<existing indexes>,univentionObjectIdentifier`

Basic stats:

Total users created: 40500  
Total user creation time: 0 days 15:27:24.030000  
average user creation time: 1.3739605916195508 seconds  
groups created: 35999  
Total group creation time: 0 days 16:50:22.540000  
Average group creation times:  
overall average: 1.6809656092004897 seconds  
average for 10 member groups: 1.677587378370843 seconds  
average for 1000 member groups: 6.020785714285716 seconds  

Total users created: 39997  
Total user creation time: 0 days 13:35:34.262000  
Average user creation time: 1.2201522152215112 seconds  
Total groups created: 40037  
Total group creation time: 0 days 03:54:40.574000  
Average group creation times:  
Overall average: 0.3515764811669442 seconds 
Average for groups with 10 members: 0.3506403140313977 seconds  
Average for groups with 1000 members: 1.28765 seconds  


## Individual load test results

Base Scenario:

- every user has a profile picture of 100kb
- 100k Users in AD
- Every user is in one extra group with a maximum group size of 100
- => 100k / 100 = 1k Groups
- UDM adds every user to the same default primary group
- No LDAP index for `univentionObjectIdentifier`
- The LDAP database is written to a Ceph-based pvc


### Initial load test attempt
For more info, see the comments on [this issue](https://git.knut.univention.de/univention/customers/dataport/team-souvap/-/issues/903)

**this is without any group syncs**
because the user sync was aborted around 35k users and group sync happens only after the user sync.

### Disable primary group


Scenario modifications:

- ~~UDM adds every user to the same default primary group~~
- primary group updates are disabled

**this is without any group syncs**
because the user sync was aborted around 80k users
and group sync happens only after the user sync.

User sync durations with linear scale:

![user-create-durations](./results_2025-02/80k-ceph-line_users_time-delta.png)

User sync durations with logarythmic scale:

![user-create-durations_logarythmic](./results_2025-02/80k-ceph-line_users_time-delta-logarythmic.png)

Number of users created over time:

![user-created-over-time](./results_2025-02/80k-local-storage_users_over-time.png)

### Index for univentionObjectIdentifier

Scenario modifications:

- ~~UDM adds every user to the same default primary group~~
- primary group updates are disabled
- ~~No LDAP index for `univentionObjectIdentifier`~~
- Added LDAP equality (`eq`) index for `univentionObjectIdentifier` via UCR

Basic stats:

Total users created: 40500  
Total user creation time: 0 days 15:27:24.030000  
average user creation time: 1.3739605916195508 seconds  

User sync durations with linear scale:

![user-create-durations](./results_2025-02/100k-ldap-index-failed-group_users_cleaned_time-delta.jpeg)

User sync durations with logarythmic scale:

![user-create-durations_logarythmic](./results_2025-02/100k-ldap-index-failed-group_users_cleaned_time-delta-logarythmic.jpeg)

Number of users created over time:

![user-created-over-time](./results_2025-02/100k-ldap-index-failed-group_users_cleaned_over-time.jpeg)


### More groups

Scenario modifications:

- ~~100k Users in AD~~
- 40k Users in AD (to make the LDAP index unnecessary)
- ~~Every user is in one extra group with a maximum group size of 100~~
- ~~=> 100k / 100 = 1k Groups~~
- Every user is in one extra group with a maximum group size of 1000 and
in 10 groups with a maximum group size of 10
- => 40k / 1k + 40k / 10 * 10 = 40040 Groups = 40k Groups
To measure the performance with a 1:1 ratio of users and groups.
- ~~UDM adds every user to the same default primary group~~
- primary group updates are disabled
- ~~The LDAP database is written to a Ceph-based pvc~~
- The LDAP database is written to a local-storage pvc. Significantly increasing the IO performance

**This load test was executed in parallel with the one above.**
This may have affected the local storage IO performance.

Basic stats:

Total users created: 39997  
Total user creation time: 0 days 13:35:34.262000  
Average user creation time: 1.2201522152215112 seconds  
Total groups created: 40037  
Total group creation time: 0 days 03:54:40.574000  
Average group creation times:  
Overall average: 0.3515764811669442 seconds 
Average for groups with 10 members: 0.3506403140313977 seconds  
Average for groups with 1000 members: 1.28765 seconds  


User sync durations with linear scale:

![user-create-durations](./results_2025-02/40k-local-storage-scatter_users_time-delta.jpeg)

User sync durations with logarythmic scale:

![user-create-durations_logarythmic](./results_2025-02/40k-local-storage-scatter_users_time-delta-logarythmic.jpeg)

Number of users created over time:

![user-created-over-time](./results_2025-02/40k-local-storage-scatter_users_over-time.jpeg)

Group sync durations with linear scale:

![group-create-durations](./results_2025-02/40k-local-storage-scatter_groups_time-delta.jpeg)

Group sync durations with logarythmic scale:

![group-create-durations_logarythmic](./results_2025-02/40k-local-storage-scatter_groups_time-delta-logarythmic.jpeg)

Number of groups created over time:

![group-created-over-time](./results_2025-02/40k-local-storage-scatter_groups_over-time.jpeg)


### More groups with Ceph storage backend

Scenario modifications:

- ~~100k Users in AD~~
- 40k Users in AD (to make the LDAP index unnecessary)
- ~~Every user is in one extra group with a maximum group size of 100~~
- ~~=> 100k / 100 = 1k Groups~~
- Every user is in one extra group with a maximum group size of 1000 and
in 10 groups with a maximum group size of 10
- => 40k / 1k + 40k / 10 * 10 = 40040 Groups = 40k Groups
To measure the performance with a 1:1 ratio of users and groups.
- ~~UDM adds every user to the same default primary group~~
- primary group updates are disabled
- The LDAP database is written to a Ceph-based pvc

**This load test was executed in parallel with the one above.**
It looks like the above test significantly affected the Ceph IO performance.

Basic stats:

Total users created: 40500  
Total user creation time: 0 days 15:27:24.030000  
average user creation time: 1.3739605916195508 seconds  

groups created: 35999  
Total group creation time: 0 days 16:50:22.540000  
Average group creation times:  
overall average: 1.6809656092004897  seconds 
average for 10 member groups: 1.677587378370843 seconds  
average for 1000 member groups: 6.020785714285716 seconds  

User sync durations with linear scale:

![user-create-durations](./results_2025-02/40k-ceph-pvc-scatter_users_time-delta.jpeg)

User sync durations with logarythmic scale:

![user-create-durations_logarythmic](./results_2025-02/40k-ceph-pvc-scatter_users_time-delta-logarythmic.jpeg)

Number of users created over time:

![user-created-over-time](./results_2025-02/40k-ceph-pvc-scatter_users_over-time.jpeg)

Group sync durations with linear scale:

![group-create-durations](./results_2025-02/40k-ceph-pvc-scatter_groups_time-delta.jpeg)

Group sync durations with logarythmic scale:

![group-create-durations_logarythmic](./results_2025-02/40k-ceph-pvc-scatter_groups_time-delta-logarythmic.jpeg)

Number of groups created over time:

![group-created-over-time](./results_2025-02/40k-ceph-pvc-scatter_groups_over-time.jpeg)
