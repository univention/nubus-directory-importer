# -*- coding: ascii -*-
"""
udm_directory_connector.connector - the connector
"""

import logging
import time
import copy

import ldap
from ldap.ldapobject import ReconnectLDAPObject
from ldap.controls.pagedresults import SimplePagedResultsControl

from junkaptor.trans import TransformerSeq

from .cfg import ConnectorConfig
from .udm import UDMMethod, UDMModel, UDMClient
from .trans import MemberRefsTransformer
from . import gen_password


class Connector:
    """
    The connector for syncing data
    """

    __slots__ = (
        '_cfg',
        '_error_count',
        '_ldap_conn',
        '_src_results_count',
        '_udm',
        'user_single_val_attrs',
        'group_single_val_attrs',
    )

    _cfg: ConnectorConfig
    _error_count: int
    _ldap_conn: ReconnectLDAPObject
    _src_results_count: int
    _udm: UDMClient

    def __init__(
            self,
            cfg: ConnectorConfig,
        ):
        self._cfg = cfg
        self._udm = UDMClient(
            self._cfg.udm.uri,
            self._cfg.udm.user,
            self._cfg.udm.password,
            self._cfg.udm.user_ou,
            self._cfg.udm.group_ou,
            self._cfg.udm.ca_cert,
            self._cfg.udm.skip_writes,
            connect_timeout = self._cfg.udm.connect_timeout,
            read_timeout = self._cfg.udm.read_timeout,
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
            new_conn_uri = self._cfg.src.ldap_uri.initializeUrl()
            new_conn = ReconnectLDAPObject(
                new_conn_uri,
                trace_level=self._cfg.src.trace_level,
            )
            new_conn.timeout = self._cfg.src.timeout
            new_conn.network_timeout = self._cfg.src.timeout
            new_conn.set_option(ldap.OPT_REFERRALS, 0)
            new_conn.set_option(ldap.OPT_X_TLS_CACERTFILE, self._cfg.src.ca_cert)
            new_conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            new_conn.simple_bind_s(self._cfg.src.bind_dn, self._cfg.src.bind_pw)
            try:
                wai = new_conn.whoami_s()
            except ldap.PROTOCOL_ERROR:
                if self._cfg.src.bind_dn:
                    wai = self._cfg.src.bind_dn
                else:
                    raise
            self._ldap_conn = new_conn
            logging.debug(
                'Successfully connected to source %s as %s',
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
        page_size = self._cfg.src.search_pagesize
        ignore_dn_regex = self._cfg.src.ignore_dn_regex
        paged_search = (page_size > 0)
        search_ctrls = []
        if paged_search > 0:
            paged_results_control = SimplePagedResultsControl(True, size=page_size, cookie=b'')
            search_ctrls.append(paged_results_control)
        logging.debug('Search entries with filter %r', ldap_filter)
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
                #logging.debug('rtype = %r, rdata = %r, _, rctrls = %r', rtype, rdata, _, rctrls)
                for rdat in rdata:
                    if isinstance(rdat[0], str):
                        if (
                                ignore_dn_regex is not None
                                and ignore_dn_regex.match(rdat[0])
                            ):
                            logging.debug('Skipping ignore_dn_regex matching %s', rdat[0])
                            continue
                        rentry = rdat[1]
                        for range_attr in range_attrs:
                            if range_attr not in rentry or rentry[range_attr]:
                                # range value attribute not in entry at all
                                # => no value ranges to retrieve
                                break
                            range_prefix = f'{range_attr};range='
                            for atype in list(rentry.keys()):
                                if not atype.startswith(range_prefix):
                                    # no range value prefix => skip this attribute
                                    continue
                                range_count = 1
                                range_values = rentry.pop(atype)
                                while True:
                                    # parse something like member;range=0-1499
                                    range_lower, range_upper = atype[len(range_prefix):].split('-', 1)
                                    logging.debug(
                                        'range_attr = %r, range_lower = %r, range_upper = %r',
                                        range_attr, range_lower, range_upper,
                                    )
                                    if range_upper == '*':
                                        logging.debug(
                                            'Retrieved %d values for attribute %r in %d chunks',
                                            len(range_values),
                                            range_attr,
                                            range_count
                                        )
                                        # finally over-write the attribute list
                                        rdat[1][range_attr] = range_values
                                        break
                                    range_lower, range_upper = int(range_lower), int(range_upper)
                                    rentry = ldap_conn.search_ext_s(
                                        rdat[0],
                                        ldap.SCOPE_BASE,
                                        filterstr='(objectClass=*)',
                                        attrlist=[f'{range_attr};range={range_upper+1}-{range_upper+range_upper-range_lower+1}'],
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
                    logging.debug('Received %d pages', result_pages)
                    if not rctrls or not rctrls[0].cookie:
                        paging_continues = False
                    # Copy cookie from response control to request control
                    paged_results_control.cookie = rctrls[0].cookie
            except (
                    ldap.NO_SUCH_OBJECT,
                    ldap.SIZELIMIT_EXCEEDED,
                    ldap.ADMINLIMIT_EXCEEDED,
                ) as err:
                logging.error('Aborting because of error: %s', err)
                break
        # end of .source_search()

    def log_summary(
            self,
            sync_start_time: float,
            src_results_count: int,
            delete_count: int,
            error_count: int,
        ):
        logging.info(
            'Finished sync of %d entries from source %s in %0.2f secs',
            src_results_count,
            self._cfg.src.ldap_uri,
            time.time()-sync_start_time,
        )
        if error_count:
            logging.error(
                '%d errors when processing source entries from %s',
                error_count, self._cfg.src.ldap_uri,
            )
        if delete_count:
            logging.info('Removed %d obsolete target entries', delete_count)
        for method in UDMMethod:
            for model in UDMModel:
                if self._udm._req_count[method.value][model.value]:
                    logging.info(
                        'UDM request count: %r %r count=%d',
                        method.value, model.value, self._udm._req_count[method.value][model.value],
                    )
                for status, count in self._udm._status_count[method.value][model.value].items():
                    logging.info(
                        '%r %r status=%d count=%d',
                        method.value, model.value, status, count,
                    )

    def delete_old_entries(self, model, old_users, id2dn):
        """
        delete entries which do not exists in source anymore
        """
        ctr = 0
        for old_pkey in old_users:
            if old_pkey not in id2dn:
                try:
                    udm_res = self._udm.delete(
                        model,
                        old_users[old_pkey][0],
                    )
                except Exception as err:
                    logging.warning('Error removing target %s entry %s: %s', model.value, old_pkey, err)
                else:
                    ctr += 1
                    logging.info('Removed target %s entry %s', model.value, old_pkey)
        return ctr

    def _prep_updates(self, model, props_list, new_props, old_props) -> dict:
        #from pprint import pformat
        #PFORMAT_KWARGS = dict(indent=2, width=50)
        #logging.debug('props_list = %s', pformat(props_list, **PFORMAT_KWARGS))
        #logging.debug('new_props = %s', pformat(new_props, **PFORMAT_KWARGS))
        #logging.debug('old_props = %s', pformat(old_props, **PFORMAT_KWARGS))
        tmpl_props = self._udm.get_template(model)['properties']
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
                    '%s property %r differs: old = %r new = %r => modify needed',
                    model, key, old_prop, new_prop,
                )
                update_props[key] = new_prop
        return update_props

    def _target_entries(self):
        """
        returns 2-tuple of dict instances containing existing target entries
        """
        users = self._udm.list(
            UDMModel.USER,
            self._cfg.udm.user_pkey_property,
            position=f'{self._cfg.udm.user_ou},{self._udm.base_position}',
            properties=self._cfg.udm.user_properties,
        )
        groups = self._udm.list(
            UDMModel.GROUP,
            self._cfg.udm.group_pkey_property,
            position=f'{self._cfg.udm.group_ou},{self._udm.base_position}',
            #properties=self._cfg.udm.group_properties,
        )
        return users, groups

    def sync_entries(
            self,
            model,
            position,
            source,
            pkey,
            properties,
            trans,
            old_entries,
        ):
        new_id2dn = {}
        src_results_count = error_count = 0
        for src_dn, src_entry in source.items():
            src_results_count += 1
            logging.debug('src_dn = %r', src_dn)
            logging.debug('src_entry = %r', src_entry)
            try:
                target_props = self._udm.prep_properties(model, trans(src_entry))
            except Exception as err:
                logging.error(
                    'Error transforming to target properties, src_entry = %r : %s',
                    src_entry,
                    err,
                    exc_info=__debug__,
                )
                error_count += 1
                continue
            logging.debug('target_props = %r', target_props)
            target_pkey = target_props[pkey]
            try:
                if target_pkey in old_entries:
                    update_props = self._prep_updates(
                        model,
                        properties,
                        target_props,
                        old_entries[target_pkey][1],
                    )
                    # TODO: move user properties update logic to user model
                    # if model == UDMModel.USER and 'mailPrimaryAddress' in update_props.keys():
                    #     del update_props['mailPrimaryAddress']
                    target_dn = old_entries[target_pkey][0]
                    new_id2dn[target_pkey] = target_dn
                    if not update_props:
                        # skip processing current entry
                        continue
                    udm_res = self._udm.modify(
                        model,
                        target_dn,
                        update_props,
                        position = position,
                    )
                    logging.info(
                          'Modified %s entry %s with primary key %r: %s',
                        model.value,
                        target_dn,
                        target_pkey,
                        ', '.join(update_props.keys()),
                    )
                else:
                    # TODO: move user properties update logic to user model
                    if model == UDMModel.USER:
                        target_props['password'] = gen_password()
                        # target_props['mailPrimaryAddress'] = target_props['e-mail'][0]
                    udm_res = self._udm.add(
                        model,
                        target_props,
                        position = position,
                    )
                    # FIX ME!
                    # We always have to compose the DNs even with UCS 5+ because
                    # in case skip_writes: true is used there's no real UDM response.
                    # Basically skip_writes: true sucks!
                    if model == UDMModel.USER:
                        target_dn = f'uid={target_props["username"]},{position}'
                    elif model == UDMModel.GROUP:
                        target_dn = f'cn={target_props["name"]},{position}'
                    new_id2dn[target_pkey] = target_dn
                    logging.info(
                        'Added %s entry %s with primary key %r',
                        model.value,
                        target_dn,
                        target_pkey,
                    )
            except Exception as err:
                logging.error(
                    'UDMError adding/modifying %s from %s: %s',
                    target_props,
                    src_dn,
                    err,
                    exc_info = __debug__,
                )
                error_count += 1
        #logging.debug('new_id2dn = %r', new_id2dn)
        # remove obsolete entries not found in source
        delete_count = self.delete_old_entries(model, old_entries, new_id2dn)
        return src_results_count, error_count, delete_count, new_id2dn
        # end of .sync_entries()

    def __call__(self):
        """
        run the sync process one time
        """
        sync_start_time = time.time()
        old_users, old_groups = self._target_entries()
        #logging.debug('old_users = %r', old_users)
        #logging.debug('old_groups = %r', old_groups)
        logging.info(
            'Found %d existing entries: %d users / %d groups',
            len(old_users)+len(old_groups), len(old_users), len(old_groups),
        )

        src_count_all = delete_count_all = error_count_all = 0

        id2dn_users = {
            pkey: dat[0]
            for pkey, dat in old_users.items()
        }
        src_users = dict(
            self.source_search(
                self._cfg.src.user_base,
                self._cfg.src.user_scope,
                self._cfg.src.user_filter,
                self._cfg.src.user_attrs,
                self._cfg.src.user_range_attrs,
            )
        )
        src_count, error_count, delete_count, id2dn = self.sync_entries(
            UDMModel.USER,
            f'{self._cfg.udm.user_ou},{self._udm.base_position}',
            src_users,
            self._cfg.udm.user_pkey_property,
            self._cfg.udm.user_properties,
            self._cfg.src.user_trans,
            old_users,
        )
        src_count_all += src_count
        delete_count_all += delete_count
        error_count_all += error_count
        id2dn_users.update(id2dn)
        logging.debug('id2dn_users = %r', id2dn_users)

        id2dn_groups = {
            pkey: dat[0]
            for pkey, dat in old_groups.items()
        }
        logging.debug('id2dn_groups = %r', id2dn_groups)
        src_groups = dict(
            self.source_search(
                self._cfg.src.group_base,
                self._cfg.src.group_scope,
                self._cfg.src.group_filter,
                self._cfg.src.group_attrs,
                self._cfg.src.group_range_attrs,
            )
        )
        src_count, error_count, delete_count, _ = self.sync_entries(
            UDMModel.GROUP,
            f'{self._cfg.udm.group_ou},{self._udm.base_position}',
            src_groups,
            self._cfg.udm.group_pkey_property,
            self._cfg.udm.group_properties,
            TransformerSeq((
                self._cfg.src.group_trans,
                MemberRefsTransformer(
                    self._cfg.udm.user_pkey_property,
                    self._cfg.src.user_trans,
                    src_users,
                    id2dn_users,
                    self._cfg.udm.group_pkey_property,
                    self._cfg.src.group_trans,
                    src_groups,
                    id2dn_groups,
                ),
            )),
            old_groups,
        )
        src_count_all += src_count
        delete_count_all += delete_count
        error_count_all += error_count

        # finally log summary messages
        self.log_summary(sync_start_time, src_count_all, delete_count_all, error_count_all)

        # return counters as result mainly for automated tests
        return (src_count_all, delete_count_all, error_count_all)
