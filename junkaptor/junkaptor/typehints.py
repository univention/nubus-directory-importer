# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
junkaptor.typehints - typing information
see https://code.stroeder.com/pymod/junkaptor

(c) 2022 by Michael Stroeder <michael@stroeder.com>

This software is distributed under the terms of the
Apache License Version 2.0 (Apache-2.0)
https://www.apache.org/licenses/LICENSE-2.0
"""

from typing import Dict, List, Sequence

BytesList = List[bytes]

StrList = List[str]

DataRecord = Dict[str, BytesList]
DataRecords = Sequence[DataRecord]
