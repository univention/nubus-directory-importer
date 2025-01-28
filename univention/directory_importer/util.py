# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import time
from typing import Callable


class Repeater:
    """
    Utility to call a callable repeatedly with an adjustable delay.
    """

    DEFAULT_DELAY = 300

    def __init__(self, target: Callable, delay: float | None = None):
        self.target = target
        if delay is None:
            delay = Repeater.DEFAULT_DELAY
        self.delay = delay

    def call(self, *args, **kwargs):
        while True:
            self.target(*args, **kwargs)
            time.sleep(self.delay)
