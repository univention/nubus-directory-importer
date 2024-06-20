# -*- coding: ascii -*-
"""
udm_directory_connector.udm - simple UDM API wrapper

Limited functionality - not meant for general use!!!
"""

import copy
import enum
import logging
import socket
import urllib.parse
from collections import defaultdict
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Sequence,
    Tuple,
)

import ldap
import requests

from junkaptor import decode_list

from .__about__ import __version__

JSON_MIME_TYPE = 'application/json'

HTTP_USER_AGENT = f'{__name__}/{__version__}'


class UDMModel(enum.Enum):
    """
    UDM model strings used
    """
    USER: str = 'users/user'
    GROUP: str = 'groups/group'
    OU: str = 'container/ou'


class UDMMethod(enum.Enum):
    """
    UDM model strings used
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'


UDM_WRITE_METHODS = {
    UDMMethod.POST,
    UDMMethod.PUT,
    UDMMethod.DELETE,
}


class UDMClient:
    """
    Class for connecting to UDM REST API with proper authentication
    """
    encoding = 'utf-8'
    __slots__ = (
        '_base_position',
        '_ca_cert',
        '_model',
        '_password',
        '_url',
        '_username',
        '_tmpl',
        '_req_count',
        '_skip_writes',
        '_status_count',
        '_connect_timeout',
        '_read_timeout',
        '_req_method',
    )
    # instance attrs types
    _ca_cert: Optional[str]
    _model: str
    _password: str
    _url: str
    _username: str
    _req_count: Dict[str, Dict[str, int]]
    _status_count: Dict[str, Dict[str, Dict[int, int]]]

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        user_ou: str,
        group_ou: str,
        ca_cert: Optional[str] = None,
        skip_writes: bool = False,
        connect_timeout: Optional[int] = 10,
        read_timeout: Optional[int] = 1800,
    ):
        if url[-1] == '/':
            url = url[:-1]
        self._url = url
        self._username = username
        self._password = password
        self._ca_cert = ca_cert
        self._skip_writes = skip_writes
        self._tmpl = {}.fromkeys(UDMModel)
        self._req_count = self._init_counter(0)
        self._status_count = self._init_counter(defaultdict)
        self._base_position = None
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout

        self._assure_ou(user_ou)
        self._assure_ou(group_ou)

    def _assure_ou(self, ou: str):
        """Create ou tree if it does not exist"""
        base_position = ldap.dn.str2dn(self.base_position)
        ou_dn = ldap.dn.str2dn(ou)
        for i in reversed(range(len(ou_dn))):
            current_ou = ou_dn[i]
            current_position = ou_dn[i+1:]
            self.create_ou(
                name=current_ou[0][1],
                description='Created by udm connector',
                position=ldap.dn.dn2str(current_position + base_position)
            )

    @staticmethod
    def _init_counter(init):
        ctr = {}
        for method in UDMMethod:
            ctr[method.value] = {}
            for model in UDMModel:
                if init is defaultdict:
                    init_val = defaultdict(lambda: 0)
                else:
                    init_val = init
                ctr[method.value][model.value] = init_val
        return ctr

    def _url_path(self, model: UDMModel, entry_dn: str):
        return '/'.join((
            self._url,
            model.value,
            urllib.parse.quote(entry_dn.encode(self.encoding)).replace('/', '%2F'),
        ))

    def prep_properties(
            self,
            model: UDMModel,
            attrs: Dict[str, List[bytes]],
            encoding: str ='utf-8',
        ):
        """
        Convert a dict typically retrieved from LDAP with bytes value lists
        to a property dict for UDM
        """
        res: Dict[str, Union[str, list]] = {}
        single_val_attrs = set(self.single_valued_props(model))
        for key, vals in attrs.items():
            new_vals = decode_list(vals, encoding=encoding)
            if key in single_val_attrs:
                if len(new_vals) > 1:
                    raise ValueError(f'Expected only one value, got {len(new_vals):d}')
                res[key] = new_vals[0]
            else:
                res[key] = new_vals
        return res

    def request(
            self,
            method: UDMMethod,
            model: UDMModel,
            entry_dn: str = '',
            headers : Dict = None,
            params : Dict = None,
            data : Dict = None,
            read_timeout: Optional[int] = None,
        ):
        """
        Send a API request
        """
        req_url = self._url_path(model, entry_dn)
        self._req_count[method.value][model.value] += 1
        req_headers = {
            'Accept': JSON_MIME_TYPE,
            'Content-Type': JSON_MIME_TYPE,
            'User-Agent': HTTP_USER_AGENT,
        }
        req_headers.update(headers or {})
        if self._skip_writes and method in UDM_WRITE_METHODS:
            logging.debug(
                'Skipping %s request to UDM at %r, headers %r',
                method.value, req_url, req_headers
            )
            return
        logging.debug(
            'Sending %s request to UDM at %r, headers %r',
            method.value, req_url, req_headers
        )

        resp = requests.request(
            method.value,
            req_url,
            auth = (self._username, self._password),
            headers = req_headers,
            params = params,
            json = data,
            verify = self._ca_cert,
            allow_redirects = False,
            timeout = (
                self._connect_timeout,
                read_timeout
                if read_timeout is not None
                else self._read_timeout
            ),
        )
        self._status_count[method.value][model.value][resp.status_code] += 1
        logging.debug(
            'Received %s response status %d from UDM at %r: %r Etag = %r',
            method.value, resp.status_code, req_url, resp.reason, resp.headers.get('Etag')
        )
        #if resp.content:
        #    logging.debug('%s response JSON data: %s', method.value, resp.json())
        if 300 <= resp.status_code < 400:
            raise requests.HTTPError(
                f'{resp.status_code:d} Redirect: {resp.reason} for url: {resp.url} => {resp.content}',
                response=resp,
            )
        if resp.status_code in {400, 422}:
            if resp.content:
                try:
                    resp_json = resp.json()
                    resp_err_msg = resp_json['error']['message']
                except:
                    resp_err_msg = repr(resp.content)
            raise requests.HTTPError(
                f"{resp.status_code:d} Client error: {resp.reason} for {method.value} request to URL {resp.url} with data {data!r} => {resp_err_msg}",
                response=resp,
            )
        resp.raise_for_status()
        return resp

    def get_template(self, model: UDMModel):
        if self._tmpl[model] is None:
            self._tmpl[model] = self.request(UDMMethod.GET, model, 'add').json()
        return self._tmpl[model]

    @property
    def base_position(self):
        """
        return the LDAP base DN / search root configured in UCS
        """
        if self._base_position is None:
            # FIX ME! There is probably a better way to find the configured suffix.
            self._base_position = self.get_template(UDMModel.OU)['position']
        return self._base_position

    def single_valued_props(self, model: UDMModel) -> List[str]:
        tmpl = self.get_template(model)
        return [
            name
            for name in tmpl['properties']
            if not isinstance(tmpl['properties'][name], list)
        ]

    def add(
            self,
            model: UDMModel,
            properties,
            position: Optional[str] = None,
        ):
        """
        add entry with certain model and given id attribute in sub-tree
        specified by position
        """
        # prepare data for new entry
        new = copy.deepcopy(self.get_template(model))
        new['properties'].update(properties)
        if position is not None:
            new['position'] = position
        # add the new entry
        return self.request(
            UDMMethod.POST,
            model,
            data=new,
        )

    def create_ou(
            self,
            name: str,
            description: str,
            position: Optional[str] = None,
        ):
        """
        Create an OU entry (sync target container) if needed
        """
        if not self.is_object_in_udm(UDMModel.OU, name, position):
            logging.debug('Error searching existing OU by name %s', name)
            self.add(
                UDMModel.OU,
                dict(
                    name = name,
                    description = description,
                ),
                position = position,
            )

    def modify(
            self,
            model: UDMModel,
            entry_dn: str,
            properties,
            position: Optional[str] = None,
        ):
        """
        add entry with certain model and given id attribute in sub-tree
        specified by position
        """
        udm_res = self.request(UDMMethod.GET, model, entry_dn)
        etag = udm_res.headers['Etag']
        mod = udm_res.json()
        # prepare data for new entry
        mod['properties'].update(properties)
        if position is not None:
            mod['position'] = position
        # add the mod entry
        return self.request(
            UDMMethod.PUT,
            model,
            entry_dn,
            headers={
                'If-Match': etag,
            },
            data=mod,
        )

    def delete(
            self,
            model: UDMModel,
            entry_dn: str,
        ):
        """
        delete entry referenced by model and its LDAP-DN
        """
        return self.request(UDMMethod.DELETE, model, entry_dn)

    def query(
            self,
            model: UDMModel,
            prop_attr: str,
            prop_val: str,
            properties: Optional[Sequence[str]] = None,
        ):
        params = {f'query[{prop_attr}]': prop_val}
        if properties is not None:
            params['properties'] = properties
        return self.request(UDMMethod.GET, model, params=params)

    def is_object_in_udm(self, model: UDMModel, name: str, position: str) -> bool:
        """
        Check if object with provided name and position already exists
        TODO: this should be done with search on level scope, not subtree
        """
        udm_response = self.query(model, 'name', name).json()

        if udm_response['results'] != 0:
            udm_objects = udm_response['_embedded']['udm:object']
            if position in [udm_object['position'] for udm_object in udm_objects]:
                return True

        return False

    def query_dn_by_name(self, model: UDMModel, name: str) -> str:
        """
        Query the OU entry by name
        """
        udm_json = self.query(model, 'name', name, properties=['name']).json()
        if name != udm_json['_embedded']['udm:object'][0]['properties']['name']:
            raise ValueError(
                'Expected {} entry to have name == {!r}, but got {!r}'.format(
                    model,
                    name,
                    udm_json['_embedded']['udm:object'][0]['properties']['name'],
                ),
            )
        return udm_json['_embedded']['udm:object'][0]['dn']

    def user_query(self, prop_attr: str, prop_val: str):
        """
        search user entry by property
        """
        return self.query(UDMModel.USER, prop_attr, prop_val)

    def group_query(self, prop_attr: str, prop_val: str):
        """
        search group entry by property
        """
        return self.query(UDMModel.GROUP, prop_attr, prop_val)

    def list(
            self,
            model: UDMModel,
            pkey: str,
            qfilter: Optional[str] = None,
            position: Optional[str] = None,
            properties: Optional[Sequence[str]] = None,
        ) -> Dict[str, Tuple[str, Any]]:
        """
        returns dict {properties[pkey]: (dn, properties)} of existing target entries
        """
        params = dict()
        if qfilter is not None:
            params['filter'] = qfilter
        if position is not None:
            params['position'] = position
        if properties is not None:
            params['properties'] = properties
        udm_res = self.request(UDMMethod.GET, model, params=params)
        udm_json = udm_res.json()
        entries = {}
        if udm_json['results'] > 0:
            entries = {
                res['properties'][pkey]: (
                    res['dn'], res['properties']
                )
                for res in udm_json['_embedded']['udm:object']
            }
        logging.debug('Received %d %s results from UDM', len(entries), model)
        return entries
