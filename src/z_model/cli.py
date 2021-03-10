# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = z_model.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import argparse
import sys
import logging

from z_model import __version__
from z_model.assumptions import Assumptions
from z_model.scenarios import Scenarios
from z_model.account_data import AccountData
from z_model.exeutor import Executor

__author__ = "Geyer Bisschoff"
__copyright__ = "Geyer Bisschoff"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Z-model CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Z-model {__version__}")
    parser.add_argument(
        dest="assumptions",
        help="file path to ASSUMPTIONS.xlsx",
        type=str,
        metavar="A")
    parser.add_argument(
        dest="scenarios",
        help="file path to SCENARIOS.xlsx",
        type=str,
        metavar="S")
    parser.add_argument(
        dest="account_data",
        help="file path to account_level_data.xlsx",
        type=str,
        metavar="D")
    parser.add_argument(
        dest="outfile",
        help="output file path",
        type=str,
        metavar="O")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO)
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting crazy calculations...")


    assumptions = Assumptions.from_file(url=args.assumptions)
    scenarios = Scenarios.from_file(url=args.scenarios)
    account_data = AccountData.from_file(url=args.account_data)

    results = Executor(method='process_map').execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios
    )

    results.long.to_csv(args.outfile, index=False)

    _logger.info("Done.")


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
