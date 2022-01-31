#!/usr/bin/env python
# coding: utf8

""" Centralized logging facilities. """

import logging
from pathlib import Path
from datetime import datetime

from typer import echo

logfile = Path.home() / 'logs' /'Z-model' / f'{datetime.now().strftime(format="%Y-%m-%d")}.log'
logfile.parent.mkdir(parents=True, exist_ok=True)

class TyperLoggerHandler(logging.Handler):
    """ A custom logger handler that use Typer echo. """

    def emit(self, record: logging.LogRecord) -> None:
        echo(self.format(record))

format = "[%(asctime)s] %(levelname)s: %(name)s: %(message)s"
formatter = logging.Formatter(format)
logging.basicConfig(
    filename=logfile,
    level=logging.DEBUG,
    format=format,
)
handler = TyperLoggerHandler()
handler.setFormatter(formatter)
logger: logging.Logger = logging.getLogger('Z-Model')
logger.addHandler(handler)