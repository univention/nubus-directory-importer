# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.sanitize - low-level data sanitizer functions
"""

import uuid
from functools import partial

import phonenumbers

# Default phone region (backward compatibility)
PHONE_REGION_DEFAULT = "DE"

# Default phone prefix map for German numbers (backward compatibility)
PHONE_PREFIX_MAP_DEFAULT = (
    ("+049 ", "+49"),
    ("+0", "0"),
)


def create_phone_sanitizer(region: str = PHONE_REGION_DEFAULT, prefix_map=None):
    """
    Create a phone sanitizer function with configurable region and prefix map.
    
    Args:
        region: ISO country code (e.g., "DE", "US", "GB") for parsing numbers without country prefix
        prefix_map: Optional list of (old_prefix, new_prefix) tuples for prefix normalization.
                   If None, uses default German prefix map for backward compatibility.
    
    Returns:
        A phone sanitizer function that takes bytes and returns bytes.
    """
    if prefix_map is None:
        prefix_map = PHONE_PREFIX_MAP_DEFAULT
    
    def phone_sanitizer(val: bytes) -> bytes:
        """
        sanitize a phone number value to an international format
        """
        val_u = val.decode("utf-8").replace("\u2013", "-").strip()
        for old, new in prefix_map:
            if val_u.startswith(old):
                val_u = new + val_u[len(old) :]
                break
        try:
            res = phonenumbers.format_number(
                phonenumbers.parse(
                    val_u,
                    region=(None if val_u[0] == "+" else region),
                ),
                phonenumbers.PhoneNumberFormat.INTERNATIONAL,
            ).encode("ascii")
        except phonenumbers.phonenumberutil.NumberParseException as err:
            raise ValueError(f"{val_u!r} cannot be parsed as valid phone number") from err
        return res
    
    return phone_sanitizer


# Default phone sanitizer for backward compatibility
phone_sanitizer = create_phone_sanitizer()


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
