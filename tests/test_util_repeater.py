# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from unittest import mock

import pytest

from univention.directory_importer import util


class StopException(Exception):
    """Utility to ensure that repeating forever will stop."""


@pytest.fixture(autouse=True)
def super_short_default_delay(mocker):
    mocker.patch.object(util.Repeater, "DEFAULT_DELAY", 0.001)


def test_calls_target_multiple_times():
    stub_callable = mock.Mock(
        side_effect=[None, None, StopException("STOP")],
    )
    repeat = util.Repeater(target=stub_callable)
    with pytest.raises(StopException):
        repeat.call()

    assert stub_callable.call_count == 3


def test_sleeps_by_default(mocker):
    sleep_mock = mocker.patch("time.sleep")
    stub_callable = mock.Mock(
        side_effect=[None, StopException("STOP")],
    )
    repeat = util.Repeater(target=stub_callable)
    with pytest.raises(StopException):
        repeat.call()

    sleep_mock.assert_called_once_with(util.Repeater.DEFAULT_DELAY)


@pytest.mark.parametrize("custom_delay", [0.2, 0])
def test_sleeps_a_custom_amount(mocker, custom_delay):
    sleep_mock = mocker.patch("time.sleep")
    stub_callable = mock.Mock(
        side_effect=[None, StopException("STOP")],
    )

    repeat = util.Repeater(target=stub_callable, delay=custom_delay)
    with pytest.raises(StopException):
        repeat.call()

    sleep_mock.assert_called_once_with(custom_delay)


def test_passes_arguments_to_target():
    stub_callable = mock.Mock(
        side_effect=[StopException("STOP")],
    )
    args = [1, "b"]
    kwargs = {"param": "value"}

    repeat = util.Repeater(target=stub_callable)
    with pytest.raises(StopException):
        repeat.call(*args, **kwargs)

    stub_callable.assert_called_once_with(*args, **kwargs)
