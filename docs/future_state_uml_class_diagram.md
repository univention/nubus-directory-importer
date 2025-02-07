
# Proposed State:

This is a spike result from December 2024

It represents a proposed target architecture with the knowledge gained from that spike.
Please use it as an Inspiration and documentation of our understanding at that point in time.

```mermaid

classDiagram
    Connector --> ChangeDetector
    ChangeDetector --> ChangeSynchronizer
    Transformer -- ChangeSynchronizer

    ConnectorConfig --> Connector
    UDMClient --> UDMModel
    UDMClient --> UDMMethod
    UDMClient --> UDMEntry

    ReplicationConfig --> ChangeSynchronizer

    UDMClient -- UDMConfig
    LDAPConfig --> LDAPClient

    ChangeDetector -- LDAPClient
    ChangeSynchronizer -- LDAPClient
    ChangeSynchronizer -- UDMClient

    UDMConfig --> UDMClient

    SourceConfig --> ChangeDetector

    class LDAPConfig {
        -LDAPUrl ldap_uri
        -str bind_dn
        -bytes password
        -str ca_cert
        -int search_pagesize
        -float timeout
    }

    class SourceConfig {
        -str user_base
        -int user_scope
        -str user_filter
        -str group_base
        -int group_scope
        -str group_filter
        +__init__(yaml)
    }

    class ReplicationConfig {
        -Sequence~str~ user_attrs
        -Sequence~str~ user_range_attrs
        -Transformer user_trans
        -Sequence~str~ group_attrs
        -Sequence~str~ group_range_attrs
        -Transformer group_trans
        -bool skip_writes
        -str user_ou
        -str group_ou
        -str user_primary_key_property
        -str group_primary_key_property
        +__init__(yaml)
    }

    class UDMConfig {
        -str uri
        -str user
        -str password
        -str ca_cert
        -float timeout
        +__init__(yaml)
    }

    class ConnectorConfig {
        -int trace_level
        - str log_level
        - str config_file_path
    }

    class Connector {
        ConnectorConfig connector_config
        LDAPClient ldap_client
        UDMClient udm_client
        ChangeDetector change_detector
        ChangeSynchronizer change_synchronizer
        +run()
    }

    class ChangeDetector {
        LDAPClient ldap_client
        +check_replication_status_in_database()
        +get_changed_objects() -> list[primary_key/dn]
    }

    class Transformer {
        TransformerConfig transformer_config
        +__init__()
        +transform_entry()
    }

    class UDMModel {
        <<enumeration>>
        +USER : str = "users/user"
        +GROUP : str = "groups/group"
        +OU : str = "container/ou"
    }

    class UDMMethod {
        <<enumeration>>
        +GET
        +POST
        +PUT
        +DELETE
        +OPTIONS
    }

    class UDMEntry {
        +str source_primary_key
        +str dn
        +dict properties
    }

    class UDMClient {
    }


```
