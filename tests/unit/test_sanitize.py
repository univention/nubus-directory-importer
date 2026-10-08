# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pytest

from univention.directory_importer.sanitize import str2bool


@pytest.mark.parametrize(
    "val",
    [b"true", b"TRUE", b"True", b"yes", b"YES", b"1", b"on", b"ON", b"ok", b"OK", b" true "],
)
def test_str2bool_true(val):
    assert str2bool(val) is True


@pytest.mark.parametrize(
    "val",
    [b"false", b"FALSE", b"False", b"no", b"NO", b"0", b"off", b"OFF", b"not", b"Not", b" false "],
)
def test_str2bool_false(val):
    assert str2bool(val) is False


@pytest.mark.parametrize("val", [b"", b"maybe", b"2", b"tRuE_not", b"nope"])
def test_str2bool_invalid(val):
    with pytest.raises(ValueError):
        str2bool(val)
