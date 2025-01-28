# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.__main__ - CLI entry point
"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from .__about__ import __version__
from .config import ConnectorConfig
from .connector import Connector

# log format to use when logging to console
CONSOLE_LOG_FORMAT = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False,
)


def setup_logging(log_level: str = "INFO") -> None:
    logging.captureWarnings(True)
    formatter = logging.Formatter(fmt=CONSOLE_LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)


@app.command()
def cli(
    config_filename: Annotated[
        Path,
        typer.Argument(
            envvar="AD2UCS_CFG",
            help="Path to the configuration file.",
            file_okay=True,
            dir_okay=False,
            exists=True,
            readable=True,
        ),
    ],
    log_level: Annotated[
        str,
        typer.Option(
            envvar="LOG_LEVEL",
            help="Configuration of the logging level, e.g. warning, info, debug",
        ),
    ] = "INFO",
    log_conf: Annotated[
        Optional[Path],
        typer.Option(
            envvar="LOG_CONF",
            help="Logging configuration file to configure the logging subsystem. "
            "See: https://docs.python.org/3/library/logging.config.html#logging-config-fileformat.",
            file_okay=True,
            dir_okay=False,
            exists=True,
            readable=True,
        ),
    ] = None,
):
    """
    entry-point for invocation on command-line
    """

    proc_name = os.path.basename(os.path.split(sys.argv[0])[-2])

    if log_conf:
        logging.config.fileConfig(log_conf)
    else:
        setup_logging(log_level.upper())

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
    app()
