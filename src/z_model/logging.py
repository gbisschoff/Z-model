#!/usr/bin/env python
# coding: utf8

""" Centralized logging facilities. """

import logging

from typer import echo


class TyperLoggerHandler(logging.Handler):
    """ A custom logger handler that use Typer echo. """

    def emit(self, record: logging.LogRecord) -> None:
        echo(self.format(record))

formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(name)s: %(message)s")
handler = TyperLoggerHandler()
handler.setFormatter(formatter)
logger: logging.Logger = logging.getLogger('Z-Model')
logger.addHandler(handler)


def configure_logger(verbose: bool) -> None:
    """
    Configure application logger.

    :param verbose: Print verbose logging information.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
