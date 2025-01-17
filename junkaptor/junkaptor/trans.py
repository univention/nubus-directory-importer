# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
junkaptor.trans - data transformation
see https://code.stroeder.com/pymod/junkaptor

(c) 2022 by Michael Stroeder <michael@stroeder.com>

This software is distributed under the terms of the
Apache License Version 2.0 (Apache-2.0)
https://www.apache.org/licenses/LICENSE-2.0
"""

import logging
import re
from collections import OrderedDict, defaultdict
from typing import Sequence

from . import SingleValueDict, encode_mixed_list, import_callable

__all__ = [
    "Transformer",
]


class Transformer:
    """
    Class for transforming a single data record
    """

    __slots__ = (
        "_log",
        "_encoding",
        # config
        "_fixed_attrs",
        "_fallback_attrs",
        "_rename_attrs",
        "_remove_attrs",
        "_compose_attrs",
        "_decompose_attrs",
        "_recode_attrs",
        "_remove_values",
        "_replace_values",
        "_name_suffix",
        "_single_val_attrs",
        "_sanitizer",
    )

    _encoding: str

    def __init__(
        self,
        encoding: str = "utf-8",
        fixed_attrs=None,
        fallback_attrs=None,
        rename_attrs=None,
        remove_attrs=None,
        compose_attrs=None,
        decompose_attrs=None,
        recode_attrs=None,
        remove_values=None,
        replace_values=None,
        name_suffix=None,
        single_val_attrs=None,
        sanitizer=None,
    ):
        self._encoding = encoding
        self._log = logging.getLogger(
            self.__class__.__module__ + "." + self.__class__.__name__,
        )
        self._rename_attrs = rename_attrs or {}
        self._recode_attrs = recode_attrs or {}
        self._remove_attrs = remove_attrs or []
        self._single_val_attrs = single_val_attrs or []
        self._compose_attrs = compose_attrs or {}
        self._name_suffix = name_suffix or {}
        self._sanitizer = {}
        for key, vals in (sanitizer or {}).items():
            if not isinstance(vals, (tuple, list)):
                vals = [vals]
            self._sanitizer[key] = tuple(
                [val if callable(val) else import_callable(val) for val in vals],
            )
        self._fixed_attrs = {
            key: encode_mixed_list(vals, encoding=self._encoding)
            for key, vals in (fixed_attrs or {}).items()
        }
        self._fallback_attrs = {
            key: encode_mixed_list(vals, encoding=self._encoding)
            for key, vals in (fallback_attrs or {}).items()
        }
        self._remove_values = {
            key: encode_mixed_list(vals, encoding=self._encoding)
            for key, vals in (remove_values or {}).items()
        }
        self._replace_values = {
            key: {
                old_val.encode(self._encoding): new_val.encode(self._encoding)
                for old_val, new_val in val_map.items()
            }
            for key, val_map in (replace_values or {}).items()
        }
        self._decompose_attrs = {
            key: [re.compile(val.encode(self._encoding)) for val in vals]
            for key, vals in (decompose_attrs or {}).items()
        }

    @staticmethod
    def _apply_decompose_attrs(patterns, vals):
        entry = defaultdict(lambda: [])
        for val in vals:
            for rep in patterns:
                res = rep.search(val)
                if res is None:
                    # no match at all, continue with loop
                    continue
                for key in res.groupdict():
                    if res[key] is not None:
                        entry[key].append(res[key])
                # exit after first match
                break
        return dict(entry)

    def __call__(self, record):
        src_record = dict(record)
        # process parameter decompose_attrs to extract possibly
        # multiple attributes from single attribute values
        for key, vals in record.items():
            if key in self._decompose_attrs:
                src_record.update(
                    self._apply_decompose_attrs(self._decompose_attrs[key], vals),
                )
        res = {}
        # do basic sanitizing on the source entry by processing config parameters
        # recode_attrs
        # remove_values
        # replace_values
        # and finally apply the sanitizer function defined in sanitize dict
        for key, vals in src_record.items():
            new_vals = OrderedDict()
            sani_funcs = self._sanitizer.get(key, tuple()) + self._sanitizer.get(
                "*",
                tuple(),
            )
            for val in vals:
                if not val:
                    self._log.debug("Ignoring null-length %s value", key)
                    continue
                if (
                    key in self._recode_attrs
                    and self._recode_attrs[key] != self._encoding
                ):
                    try:
                        # first check whether it's really not the correct input encoding
                        val.decode(self._encoding)
                    except UnicodeDecodeError:
                        self._log.debug(
                            "Decoding %r as %s",
                            val,
                            self._recode_attrs[key],
                        )
                        try:
                            val = val.decode(self._recode_attrs[key]).encode(
                                self._encoding,
                            )
                        except UnicodeError as err:
                            self._log.debug(
                                "Error decoding %r as %s: %s",
                                val,
                                self._recode_attrs[key],
                                err,
                            )
                            # ignore this value
                            continue
                if key in self._remove_values and val in self._remove_values[key]:
                    self._log.debug("Ignoring %s value %r", key, val)
                    continue
                if key in self._replace_values and val in self._replace_values[key]:
                    self._log.debug(
                        "Replacing %s value %r by %r",
                        key,
                        val,
                        self._replace_values[key][val],
                    )
                    val = self._replace_values[key][val]
                try:
                    new_val = val
                    for sani_func in sani_funcs:
                        new_val = sani_func(new_val)
                    new_vals[new_val] = None
                except (ValueError, UnicodeError) as err:
                    self._log.debug(
                        "Error processing %s value %r: %s",
                        key,
                        val,
                        err,
                    )
            if new_vals:
                res[key] = list(new_vals.keys())
        # process parameter rename_attrs to rename attribute types
        for key, key_old in self._rename_attrs.items():
            try:
                res[key] = res.pop(key_old)
            except KeyError:
                pass
        # process parameter fallback_attrs to add default values for
        # non-existent attributes
        for key in self._fallback_attrs:
            res[key] = res.pop(key, self._fallback_attrs[key])
        # process parameter fixed_attrs to set fixed values for
        # some attributes even if they existed
        res.update(self._fixed_attrs)
        # process parameter remove_attrs to remove some attributes completely
        for key in self._remove_attrs:
            res.pop(key, None)
        # process parameter compose_attrs to compose
        # single-valued attributes from string templates
        svd = SingleValueDict(res)
        for key, vals in self._compose_attrs.items():
            for val in vals:
                try:
                    res[key] = [val.format(**svd).encode(self._encoding)]
                except KeyError:
                    continue
                else:
                    break
        # make again sure an attribute value only appears once
        for key, vals in list(res.items()):
            new_vals = OrderedDict()
            for val in vals:
                new_vals[val] = None
            res[key] = list(new_vals.keys())
        # transform to single-value attribute
        for key in self._single_val_attrs:
            if key in res:
                if len(res[key]) > 1:
                    raise ValueError(
                        "Expected only one value, got {:d}".format(len(res[key])),
                    )
                res[key] = res.pop(key)[0]
        # add a suffix to attribute names which need it
        for key in self._name_suffix:
            if key in res:
                res[key + self._name_suffix[key]] = res.pop(key)
        return res


class TransformerSeq(Transformer):
    """
    Class for transforming a single data record by applying a sequence of Transformer instances
    """

    __slots__ = ("_transformers",)
    _transformers: Sequence[Transformer]

    def __init__(self, transformers: Sequence[Transformer]):
        self._transformers = transformers

    def __call__(self, record):
        for tf in self._transformers:
            record = tf(record)
        return record
