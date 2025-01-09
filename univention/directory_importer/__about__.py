"""
univention.directory_importer.__about__ - Meta information
"""

import collections

VersionInfo = collections.namedtuple("VersionInfo", ("major", "minor", "micro"))
__version_info__ = VersionInfo(
    major=0,
    minor=6,
    micro=3,
)
__version__ = ".".join(str(val) for val in __version_info__)
__author__ = "Univention GmbH"
__mail__ = "info@univention.de"
__copyright__ = f"(C) 2024 by {__author__} <{__mail__}>"
__license__ = "AGPL-3.0-only OR LicenseRef-Univention-Proprietary"

__all__ = [
    "__version_info__",
    "__version__",
    "__author__",
    "__mail__",
    "__license__",
    "__copyright__",
]
