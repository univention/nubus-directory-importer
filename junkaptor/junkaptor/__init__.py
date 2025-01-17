# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
junkaptor - a data sanitizer package
see https://code.stroeder.com/pymod/junkaptor

(c) 2022 by Michael Stroeder <michael@stroeder.com>

This software is distributed under the terms of the
Apache License Version 2.0 (Apache-2.0)
https://www.apache.org/licenses/LICENSE-2.0
"""

from importlib import import_module
from typing import Callable, Sequence, Union

from .typehints import BytesList, DataRecord, StrList

__all__ = [
    "decode_list",
    "encode_list",
    "SingleValueDict",
]


class SingleValueDict(dict):
    """
    dict-derived class which only stores and returns the
    first decoded str value of a bytes list
    """

    __slots__ = ("_encoding",)

    def __init__(self, entry: DataRecord, encoding: str = "utf-8"):
        dict.__init__(self)
        self._encoding = encoding
        entry = entry or {}
        for key, val in entry.items():
            self.__setitem__(key, val)

    def __setitem__(self, key: str, val: bytes):
        try:
            dict.__setitem__(self, key, val[0].decode(self._encoding))
        except UnicodeDecodeError:
            pass


def decode_list(lst: Sequence[bytes], encoding: str = "utf-8") -> StrList:
    """
    decode a sequence containing only byte-strings with given encoding
    and return a list of strings
    """
    return [item.decode(encoding) for item in lst]


def encode_list(lst: Sequence[str], encoding: str = "utf-8") -> BytesList:
    """
    encode a sequence containing only Unicode-strings with given encoding
    and return a list of bytes
    """
    return [item.encode(encoding) for item in lst]


def encode_str(val: Union[str, bytes], encoding: str = "utf-8") -> bytes:
    """
    encode a Unicode-string to bytes, leave bytes as is
    """
    return val if isinstance(val, bytes) else val.encode(encoding)


def encode_mixed_list(
    lst: Sequence[Union[str, bytes]],
    encoding: str = "utf-8",
) -> BytesList:
    """
    encode a sequence containing only Unicode-strings with given encoding
    and return a list of bytes
    """
    return [encode_str(item, encoding) for item in lst]


def import_callable(name: str) -> Callable:
    """
    Import a callable (function or class method) by name.

    Raises TypeError if name does not reference a typehints.Callable
    """
    try:
        mod_name, attr_name = name.split(":", 1)
    except ValueError:
        mod_name, attr_name = "builtins", name
    mod = import_module(mod_name)
    try:
        cls_name, method_name = attr_name.split(".", 1)
    except ValueError:
        res = getattr(mod, attr_name)
    else:
        res = getattr(getattr(mod, cls_name), method_name)
    if not callable(res):
        raise TypeError(
            f"Expected object imported by {name!r} to be callable, got {res!r}",
        )
    return res
