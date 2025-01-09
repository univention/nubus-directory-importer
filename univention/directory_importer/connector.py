# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.connector - the connector
"""

import logging
import time

import ldap
from junkaptor.trans import TransformerSeq
from ldap.controls.pagedresults import SimplePagedResultsControl
from ldap.ldapobject import ReconnectLDAPObject

from . import gen_password
from .config import ConnectorConfig
from .trans import MemberRefsTransformer
from .udm import UDMClient, UDMEntry, UDMMethod, UDMModel


class Connector:
    """
    The connector for syncing data
    """

    __slots__ = (
        "_config",
        "_error_count",
        "_ldap_conn",
        "_source_results_count",
        "_udm",
        "user_single_val_attrs",
        "group_single_val_attrs",
    )

    _config: ConnectorConfig
    _error_count: int
    _ldap_conn: ReconnectLDAPObject
    _source_results_count: int
    _udm: UDMClient

    def __init__(
        self,
        config: ConnectorConfig,
    ):
        self._config = config
        self._udm = UDMClient(
            self._config.udm.uri,
            self._config.udm.user,
            self._config.udm.password,
            self._config.udm.user_ou,
            self._config.udm.group_ou,
            self._config.udm.ca_cert,
            self._config.udm.skip_writes,
            connect_timeout=self._config.udm.connect_timeout,
            read_timeout=self._config.udm.read_timeout,
        )
        # cache var for source LDAP connection opened later
        self._ldap_conn = None

    @property
    def ldap_conn(self):
        """
        returns the bound LDAP connection based on configuration,
        initially opens connection and binds if necessary
        """
        if self._ldap_conn is None:
            new_conn_uri = self._config.src.ldap_uri.initializeUrl()
            new_conn = ReconnectLDAPObject(
                new_conn_uri,
                trace_level=self._config.src.trace_level,
            )
            new_conn.timeout = self._config.src.timeout
            new_conn.network_timeout = self._config.src.timeout
            new_conn.set_option(ldap.OPT_REFERRALS, 0)
            new_conn.set_option(ldap.OPT_X_TLS_CACERTFILE, self._config.src.ca_cert)
            new_conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            new_conn.simple_bind_s(self._config.src.bind_dn, self._config.src.bind_pw)
            try:
                wai = new_conn.whoami_s()
            except ldap.PROTOCOL_ERROR:
                if self._config.src.bind_dn:
                    wai = self._config.src.bind_dn
                else:
                    raise
            self._ldap_conn = new_conn
            logging.debug(
                "Successfully connected to source %s as %s",
                new_conn_uri,
                wai,
            )
        return self._ldap_conn

    def source_search(
        self,
        search_base: str,
        search_scope: int,
        ldap_filter: str,
        ldap_attrs,
        range_attrs,
    ):
        """
        generator for iterating over source entries
        """
        ldap_conn = self.ldap_conn
        # send a synchronous LDAP Who Am I? operation to trigger
        # reconnecting after longer silent period on LDAP connection
        ldap_conn.whoami_s()
        # start searching with simple paged results control
        page_size = self._config.src.search_pagesize
        ignore_dn_regex = self._config.src.ignore_dn_regex
        paged_search = page_size > 0
        search_ctrls = []
        if paged_search > 0:
            paged_results_control = SimplePagedResultsControl(
                True,
                size=page_size,
                cookie=b"",
            )
            search_ctrls.append(paged_results_control)
        logging.debug("Search entries with filter %r", ldap_filter)
        # do the paged search as long as a cookie is received in response control
        paging_continues = True
        result_pages = 0
        while paging_continues:
            msg_id = ldap_conn.search_ext(
                search_base,
                search_scope,
                filterstr=ldap_filter,
                attrlist=ldap_attrs,
                serverctrls=search_ctrls,
            )
            try:
                rtype, rdata, _, rctrls = ldap_conn.result3(msg_id)
                # logging.debug('rtype = %r, rdata = %r, _, rctrls = %r', rtype, rdata, _, rctrls)
                for rdat in rdata:
                    if isinstance(rdat[0], str):
                        if ignore_dn_regex is not None and ignore_dn_regex.match(
                            rdat[0],
                        ):
                            logging.debug(
                                "Skipping ignore_dn_regex matching %s",
                                rdat[0],
                            )
                            continue
                        rentry = rdat[1]
                        for range_attr in range_attrs:
                            if range_attr not in rentry or rentry[range_attr]:
                                # range value attribute not in entry at all
                                # => no value ranges to retrieve
                                break
                            range_prefix = f"{range_attr};range="
                            for atype in list(rentry.keys()):
                                if not atype.startswith(range_prefix):
                                    # no range value prefix => skip this attribute
                                    continue
                                range_count = 1
                                range_values = rentry.pop(atype)
                                while True:
                                    # parse something like member;range=0-1499
                                    range_lower, range_upper = atype[
                                        len(range_prefix) :
                                    ].split("-", 1)
                                    logging.debug(
                                        "range_attr = %r, range_lower = %r, range_upper = %r",
                                        range_attr,
                                        range_lower,
                                        range_upper,
                                    )
                                    if range_upper == "*":
                                        logging.debug(
                                            "Retrieved %d values for attribute %r in %d chunks",
                                            len(range_values),
                                            range_attr,
                                            range_count,
                                        )
                                        # finally over-write the attribute list
                                        rdat[1][range_attr] = range_values
                                        break
                                    range_lower, range_upper = int(range_lower), int(
                                        range_upper,
                                    )
                                    rentry = ldap_conn.search_ext_s(
                                        rdat[0],
                                        ldap.SCOPE_BASE,
                                        filterstr="(objectClass=*)",
                                        attrlist=[
                                            f"{range_attr};range={range_upper+1}-{range_upper+range_upper-range_lower+1}",
                                        ],
                                    )[0][1]
                                    atype = list(rentry.keys())[0]
                                    range_values.extend(rentry[atype])
                                    range_count += 1
                        yield rdat
                if rtype == ldap.RES_SEARCH_RESULT:
                    result_pages += 1
                    if not paged_search:
                        paging_continues = False
                        break
                    logging.debug("Received %d pages", result_pages)
                    if not rctrls or not rctrls[0].cookie:
                        paging_continues = False
                    # Copy cookie from response control to request control
                    paged_results_control.cookie = rctrls[0].cookie
            except (
                ldap.NO_SUCH_OBJECT,
                ldap.SIZELIMIT_EXCEEDED,
                ldap.ADMINLIMIT_EXCEEDED,
            ) as err:
                logging.error("Aborting because of error: %s", err)
                break
        # end of .source_search()

    def log_summary(
        self,
        sync_start_time: float,
        source_results_count: int,
        delete_count: int,
        error_count: int,
    ):
        logging.info(
            "Finished sync of %d entries from source %s in %0.2f secs",
            source_results_count,
            self._config.src.ldap_uri,
            time.time() - sync_start_time,
        )
        if error_count:
            logging.error(
                "%d errors when processing source entries from %s",
                error_count,
                self._config.src.ldap_uri,
            )
        if delete_count:
            logging.info("Removed %d obsolete target entries", delete_count)
        for method in UDMMethod:
            for model in UDMModel:
                if self._udm._req_count[method.value][model.value]:
                    logging.info(
                        "UDM request count: %r %r count=%d",
                        method.value,
                        model.value,
                        self._udm._req_count[method.value][model.value],
                    )
                for status, count in self._udm._status_count[method.value][
                    model.value
                ].items():
                    logging.info(
                        "%r %r status=%d count=%d",
                        method.value,
                        model.value,
                        status,
                        count,
                    )

    def delete_old_entries(self, model, old_users: dict[str, UDMEntry], id2dn):
        """
        delete entries which do not exists in source anymore
        """
        ctr = 0
        for old_primary_key in old_users:
            if old_primary_key in id2dn:
                continue
            try:
                self._udm.delete(
                    model,
                    old_users[old_primary_key].dn,
                )
            except Exception as err:
                logging.warning(
                    "Error removing target %s entry %s: %s",
                    model.value,
                    old_primary_key,
                    err,
                )
            else:
                ctr += 1
                logging.info("Removed target %s entry %s", model.value, old_primary_key)
        return ctr

    def _prep_updates(self, model, props_list, new_props, old_props) -> dict:
        # from pprint import pformat
        # PFORMAT_KWARGS = dict(indent=2, width=50)
        # logging.debug('props_list = %s', pformat(props_list, **PFORMAT_KWARGS))
        # logging.debug('new_props = %s', pformat(new_props, **PFORMAT_KWARGS))
        # logging.debug('old_props = %s', pformat(old_props, **PFORMAT_KWARGS))
        tmpl_props = self._udm.get_template(model)["properties"]
        update_props = {}

        def values_equal(old, new):
            if isinstance(new, list):
                if old is None:
                    old = []
                return sorted(old) == sorted(new)
            return old == new

        for key in props_list:
            old_prop = old_props.get(key)
            new_prop = new_props.get(key, tmpl_props[key])
            if not values_equal(old_prop, new_prop):
                logging.debug(
                    "%s property %r differs: old = %r new = %r => modify needed",
                    model,
                    key,
                    old_prop,
                    new_prop,
                )
                update_props[key] = new_prop
        return update_props

    # TODO: What does existing target entries mean?
    def _get_existing_udm_objects(
        self,
    ) -> tuple[dict[str, UDMEntry], dict[str, UDMEntry]]:
        """
        returns 2-tuple of dict instances containing existing target entries
        """
        users = self._udm.list(
            UDMModel.USER,
            self._config.udm.user_primary_key_property,
            position=f"{self._config.udm.user_ou},{self._udm.base_position}",
            properties=self._config.udm.user_properties,
        )
        groups = self._udm.list(
            UDMModel.GROUP,
            self._config.udm.group_primary_key_property,
            position=f"{self._config.udm.group_ou},{self._udm.base_position}",
            # properties=self._config.udm.group_properties,
        )
        return users, groups

        # model=UDMModel.USER,
        # position=f'{self._config.udm.user_ou},{self._udm.base_position}',
        # source=source_users,
        # primary_key=self._config.udm.user_primary_key_property,
        # properties=self._config.udm.user_properties,
        # trans=self._config.src.user_trans,
        # old_entries=old_users,

    def sync_entries(
        self,
        model: UDMModel,
        position: str,
        source,
        primary_key,
        properties,
        trans,
        old_entries: dict[str, UDMEntry],
    ):
        new_id2dn = {}
        source_results_count = error_count = 0
        for source_dn, source_entry in source.items():
            source_results_count += 1
            logging.debug("source_dn = %r", source_dn)
            logging.debug("source_entry = %r", source_entry)
            try:
                target_props = self._udm.prep_properties(model, trans(source_entry))
            except Exception as err:
                logging.error(
                    "Error transforming to target properties, source_entry = %r : %s",
                    source_entry,
                    err,
                    exc_info=__debug__,
                )
                error_count += 1
                continue
            logging.debug("target_props = %r", target_props)
            target_primary_key = target_props[primary_key]
            try:
                if target_primary_key in old_entries:
                    update_props = self._prep_updates(
                        model,
                        properties,
                        target_props,
                        old_entries[target_primary_key].properties,
                    )
                    # TODO: move user properties update logic to user model
                    # if model == UDMModel.USER and 'mailPrimaryAddress' in update_props.keys():
                    #     del update_props['mailPrimaryAddress']
                    target_dn = old_entries[target_primary_key].dn
                    new_id2dn[target_primary_key] = target_dn
                    if not update_props:
                        # skip processing current entry
                        continue
                    self._udm.modify(
                        model,
                        target_dn,
                        update_props,
                        position=position,
                    )
                    logging.info(
                        "Modified %s entry %s with primary key %r: %s",
                        model.value,
                        target_dn,
                        target_primary_key,
                        ", ".join(update_props.keys()),
                    )
                else:
                    # TODO: move user properties update logic to user model
                    if model == UDMModel.USER:
                        target_props["password"] = gen_password()
                        # target_props['mailPrimaryAddress'] = target_props['e-mail'][0]
                    self._udm.add(
                        model,
                        target_props,
                        position=position,
                    )
                    # FIX ME!
                    # We always have to compose the DNs even with UCS 5+ because
                    # in case skip_writes: true is used there's no real UDM response.
                    # Basically skip_writes: true sucks!
                    if model == UDMModel.USER:
                        target_dn = f'uid={target_props["username"]},{position}'
                    elif model == UDMModel.GROUP:
                        target_dn = f'cn={target_props["name"]},{position}'
                    new_id2dn[target_primary_key] = target_dn
                    logging.info(
                        "Added %s entry %s with primary key %r",
                        model.value,
                        target_dn,
                        target_primary_key,
                    )
            except Exception as err:
                logging.error(
                    "UDMError adding/modifying %s from %s: %s",
                    target_props,
                    source_dn,
                    err,
                    exc_info=__debug__,
                )
                error_count += 1
        # logging.debug('new_id2dn = %r', new_id2dn)
        # remove obsolete entries not found in source
        delete_count = self.delete_old_entries(model, old_entries, new_id2dn)
        return source_results_count, error_count, delete_count, new_id2dn
        # end of .sync_entries()

    def __call__(self):
        """
        run the sync process one time
        """
        sync_start_time = time.time()
        old_users, old_groups = self._get_existing_udm_objects()
        logging.info(
            "Found %d existing entries: %d users / %d groups",
            len(old_users) + len(old_groups),
            len(old_users),
            len(old_groups),
        )

        source_count_all = delete_count_all = error_count_all = 0

        id2dn_users = {user.source_primary_key: user.dn for user in old_users.values()}
        source_users = dict(
            self.source_search(
                self._config.src.user_base,
                self._config.src.user_scope,
                self._config.src.user_filter,
                self._config.src.user_attrs,
                self._config.src.user_range_attrs,
            ),
        )
        source_count, error_count, delete_count, id2dn = self.sync_entries(
            model=UDMModel.USER,
            position=f"{self._config.udm.user_ou},{self._udm.base_position}",
            source=source_users,
            primary_key=self._config.udm.user_primary_key_property,
            properties=self._config.udm.user_properties,
            trans=self._config.src.user_trans,
            old_entries=old_users,
        )
        source_count_all += source_count
        delete_count_all += delete_count
        error_count_all += error_count
        id2dn_users.update(id2dn)
        logging.debug("id2dn_users = %r", id2dn_users)

        id2dn_groups = {
            group.source_primary_key: group.dn for group in old_groups.values()
        }
        logging.debug("id2dn_groups = %r", id2dn_groups)
        source_groups = dict(
            self.source_search(
                self._config.src.group_base,
                self._config.src.group_scope,
                self._config.src.group_filter,
                self._config.src.group_attrs,
                self._config.src.group_range_attrs,
            ),
        )
        source_count, error_count, delete_count, _ = self.sync_entries(
            UDMModel.GROUP,
            f"{self._config.udm.group_ou},{self._udm.base_position}",
            source_groups,
            self._config.udm.group_primary_key_property,
            self._config.udm.group_properties,
            TransformerSeq(
                (
                    self._config.src.group_trans,
                    MemberRefsTransformer(
                        user_primary_key=self._config.udm.user_primary_key_property,
                        user_trans=self._config.src.user_trans,
                        users=source_users,
                        id2dn_users=id2dn_users,
                        group_primary_key=self._config.udm.group_primary_key_property,
                        group_trans=self._config.src.group_trans,
                        groups=source_groups,
                        id2dn_groups=id2dn_groups,
                    ),
                ),
            ),
            old_groups,
        )
        source_count_all += source_count
        delete_count_all += delete_count
        error_count_all += error_count

        # finally log summary messages
        self.log_summary(
            sync_start_time,
            source_count_all,
            delete_count_all,
            error_count_all,
        )

        # return counters as result mainly for automated tests
        return (source_count_all, delete_count_all, error_count_all)
