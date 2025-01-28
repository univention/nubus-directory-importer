# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

"""
univention.directory_importer.__main__ - CLI entry point
"""

import logging
import logging.config
from pathlib import Path
from typing import Annotated, Optional

import typer

from .__about__ import __version__
from .config import ConnectorConfig
from .connector import Connector
from .util import Repeater

# log format to use when logging to console
CONSOLE_LOG_FORMAT = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False,
)


@app.command()
def cli(
    config_filename: Annotated[
        Path,
        typer.Argument(
            envvar="CONFIG_FILENAME",
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
    repeat: Annotated[
        bool,
        typer.Option(
            envvar="REPEAT",
            help="Run the sync repeatedly forever.",
        ),
    ] = False,
    repeat_delay: Annotated[
        Optional[float],
        typer.Option(
            envvar="REPEAT_DELAY",
            help=f"Delay in seconds between repeated runs, {Repeater.DEFAULT_DELAY} seconds by default.",
        ),
    ] = None,
):
    """
    Directory importer - Sync users from a source directory into a target UDM Rest API.
    """

    if log_conf:
        logging.config.fileConfig(log_conf)
    else:
        setup_logging(log_level.upper())

    logging.info(
        "Directory importer version %s, using config %s",
        __version__,
        config_filename,
    )

    config = ConnectorConfig(config_filename)
    connector = Connector(config)
    if repeat:
        repeater = Repeater(target=connector, delay=repeat_delay)
        repeater.call()
    else:
        connector()


def setup_logging(log_level: str = "INFO") -> None:
    logging.captureWarnings(True)
    formatter = logging.Formatter(fmt=CONSOLE_LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)


if __name__ == "__main__":
    app()
