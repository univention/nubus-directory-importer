# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.__main__ - CLI entry point
"""

import logging
import logging.config
import os
import sys

from .__about__ import __version__
from .config import ConnectorConfig
from .connector import Connector

# log format to use when logging to console
CONSOLE_LOG_FORMAT = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"


def setup_logging(log_level: str = "INFO") -> None:
    logging.captureWarnings(True)
    formatter = logging.Formatter(fmt=CONSOLE_LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)


def cli():
    """
    entry-point for invocation on command-line
    """

    proc_name = os.path.basename(os.path.split(sys.argv[0])[-2])

    # Set up logging with environment variable or default
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Use LOG_CONF if specified, otherwise use setup_logging
    if "LOG_CONF" in os.environ:
        logging.config.fileConfig(os.environ["LOG_CONF"])
    else:
        setup_logging(log_level)

    # determine path name of configuration file
    try:
        config_filename = sys.argv[1]
    except IndexError:
        try:
            config_filename = os.environ["AD2UCS_CFG"]
        except KeyError:
            logging.error(
                "Starting %s %s failed, no config given",
                proc_name,
                __version__,
            )
            sys.exit(1)

    logging.info(
        "Starting %s %s, using config %s",
        proc_name,
        __version__,
        config_filename,
    )

    # read and parse source and target configuration
    config = ConnectorConfig(config_filename)
    connector = Connector(config)
    connector()

    # end of cli()


if __name__ == "__main__":
    cli()
