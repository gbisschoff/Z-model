#!/usr/bin/env python
# coding: utf8

""" Centralized logging facilities. """

import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s: %(name)s: %(message)s",
    )
