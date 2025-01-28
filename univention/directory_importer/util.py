# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import logging
import time
from typing import Callable

log = logging.getLogger(__name__)


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
        log.debug("Repeating delay set to %i", self.delay)

    def call(self, *args, **kwargs):
        while True:
            self.target(*args, **kwargs)
            log.info("Sleeping %i seconds", self.delay)
            time.sleep(self.delay)
