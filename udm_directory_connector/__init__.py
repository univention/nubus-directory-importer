# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
udm_directory_connector module package
"""

import secrets
import string

# a subset of special chars
PWD_PUNCTUATION = "-.,;:_#+*~%/"

# alphabet used for generated passwords
PWD_ALPHABET = string.ascii_letters + string.digits + PWD_PUNCTUATION


def random_str(
    alphabet: str = PWD_ALPHABET,
    length: int = 64,
) -> str:
    """
    generate a random str
    """
    res = []
    for _ in range(length):
        res.append(secrets.choice(alphabet))
    return "".join(res)


def gen_password(rounds: int = 2):
    """
    generate random password with different character classes
    for hopefully satisfying any weird password policy out there
    """
    res = []
    for _ in range(rounds):
        res.extend(
            (
                random_str(PWD_ALPHABET, 6),
                random_str(string.digits, 2),
                random_str(PWD_ALPHABET, 4),
                random_str(string.ascii_uppercase, 2),
                random_str(PWD_ALPHABET, 9),
                random_str(string.ascii_lowercase, 2),
                random_str(PWD_ALPHABET, 4),
                random_str(PWD_PUNCTUATION, 3),
            ),
        )
    return "".join(res)
