# -*- coding: ascii -*-
"""
udm_directory_connector.__main__ - CLI entry point
"""

import sys
import os
import logging
import logging.config

from .__about__ import __version__

from .config import ConnectorConfig
from .connector import Connector

# log format to use when logging to console
CONSOLE_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'


def init_logger():
    """
    Configure either a global StreamHandler logger (stderr)
    """
    logger = logging.getLogger()
    if 'LOG_CONF' in os.environ:
        logging.config.fileConfig(os.environ['LOG_CONF'])
    else:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(logging.Formatter(fmt=CONSOLE_LOG_FORMAT))
        logger.addHandler(log_handler)
    if 'LOG_LEVEL' in os.environ:
        logger.setLevel(os.environ['LOG_LEVEL'].upper())


def cli():
    """
    entry-point for invocation on command-line
    """

    proc_name = os.path.basename(os.path.split(sys.argv[0])[-2])
    init_logger()

    # determine path name of configuration file
    try:
        config_filename = sys.argv[1]
    except IndexError:
        try:
            config_filename = os.environ['AD2UCS_CFG']
        except KeyError:
            logging.error('Starting %s %s failed, no config given', proc_name, __version__)
            sys.exit(1)

    logging.info('Starting %s %s, using config %s', proc_name, __version__, config_filename)

    # read and parse source and target configuration
    config = ConnectorConfig(config_filename)
    connector = Connector(config)
    connector()

    # end of cli()


if __name__ == '__main__':
    cli()
