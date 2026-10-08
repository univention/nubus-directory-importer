# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.sanitize - low-level data sanitizer functions
"""

import uuid

import phonenumbers

PHONE_REGION = "DE"

PHONE_PREFIX_MAP = (
    ("+049 ", "+49"),
    ("+0", "0"),
)


def phone_sanitizer(val: bytes) -> bytes:
    """
    sanitize a phone number value to an international format
    """
    val_u = val.decode("utf-8").replace("\u2013", "-").strip()
    for old, new in PHONE_PREFIX_MAP:
        if val_u.startswith(old):
            val_u = new + val_u[len(old) :]
            break
    try:
        res = phonenumbers.format_number(
            phonenumbers.parse(
                val_u,
                region=(None if val_u[0] == "+" else PHONE_REGION),
            ),
            phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        ).encode("ascii")
    except phonenumbers.phonenumberutil.NumberParseException as err:
        raise ValueError(f"{val_u!r} cannot be parsed as valid phone number") from err
    return res


def unicode_strip(val: bytes) -> bytes:
    """
    sanitize the input by stripping all white-space Unicode chars
    """
    return val.decode("utf-8").strip().encode("utf-8")


def mail_sanitizer(val: bytes) -> bytes:
    """
    sanitize the input by stripping all white-space Unicode chars,
    lower-case the domain part and re-encode as ASCII to provoke UnicodeError
    with non-ASCII chars
    """
    local_part, domain_part = val.decode("utf-8").strip().rsplit("@", 1)
    return b"@".join((local_part.encode("ascii"), domain_part.lower().encode("idna")))


def guid2uuid(val: bytes) -> bytes:
    """
    returns GUID as UUID string representation
    """
    return str(uuid.UUID(bytes_le=val)).encode("ascii")


_TRUE_VALUES = frozenset((b"true", b"yes", b"1", b"on", b"ok"))
_FALSE_VALUES = frozenset((b"false", b"no", b"0", b"off", b"not"))


def str2bool(val: bytes) -> bool:
    """
    sanitize a string representation of a boolean value to a Python bool

    Accepted true values (case-insensitive): true, yes, 1, on, ok
    Accepted false values (case-insensitive): false, no, 0, off, not
    Raises ValueError for any unrecognized value.
    """
    normalized = val.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"{val!r} cannot be parsed as a boolean value")
