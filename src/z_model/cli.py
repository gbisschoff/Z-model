# -*- coding: utf-8 -*-
"""
This is a CLI that can serve as a user friendly entry point for the Z-model.

The API makes three enpoints available to the user:

* about: to print information about the current version of the Z-model;
* generate_scenarios: used to generate macroeconomic scenarios from monte-carlo assumptions; and
* run: used to run the Z-model on an account dataset and produce ECL results.

"""

import typer
from typing import Optional
import sys
import logging
from pathlib import Path

from z_model import __version__
from z_model.assumptions import Assumptions
from z_model.scenarios import Scenarios
from z_model.account import AccountData
from z_model.exeutor import Executor
from .file_reader import write_file
from .exeutor import Methods

__author__ = "Geyer Bisschoff"
__copyright__ = "Geyer Bisschoff"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

app = typer.Typer()


def setup_logging(loglevel:int):
    """Setup basic logging

    :param loglevel: minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


@app.command()
def about():
    '''
    Print Z-model about information.
    '''
    return print(
    f"""
    Z-Model
    =======================
    Version: {__version__}
    Author: {__author__}
    License: {__license__}
    Copyright: {__copyright__}
    """
    )


@app.command()
def generate_scenarios(
    assumptions: Path,
    outfile: Path,
    verbose: bool = False
):
    '''
    Generate macroeconomic scenarios using Monte Carlo

    :param assumptions: the path to the MONTE_CARLO_ASSUMPTIONS.xlsx file.
    :param outfile: the path to save the generated scenarios. Recommeded to be a .csv.gz file type.

    '''
    setup_logging(logging.INFO if not verbose else logging.DEBUG)
    _logger.info(f'Debugging level set to {logging.INFO if not verbose else logging.DEBUG}')

    _logger.info(f'Generating scenarios from monte-carlo assumptions ({assumptions=}).')
    scenarios = Scenarios.from_assumptions(url=assumptions)
    _logger.info(f'Saving monte-carlo scenarios ({outfile=}).')
    write_file(
        df=scenarios.as_dataframe(),
        url=outfile
    )
    _logger.info("Done.")


@app.command()
def run(
        account_data: Path,
        assumptions: Path,
        scenarios: Path,
        outfile: Path,
        method: Methods = Methods.Map,
        verbose: bool = False
):
    '''
    Run the Z-model on specified inputs.

    :param account_data: path to the account level data file.
        The file should be one of the supported file types.

    :param assumptions: path to the assumptions file.
        The file should be in .XLSX format.

    :param scenarios: the path to the macroeconomic scenarios.
        The file should be in .XLSX, .CSV or .CSV.GZ format.

    :param outfile: the path to the output file. Results are stored in a zip archive and thus should have the
        a `.zip` extension.

    :param monte_carlo: a flag specifying that the SCENARIOS inputs are monte-carlo assumptions and not discrete
        scenarios. A path should be provided where the generated scenarios are saved. Depending on the number of scenarios
        generated the file might become large. It is recommended to use a compressed CSV file (.csv.gz)

    :param method: one of either 'map', 'process_map' or 'thread_map'. Depending on the selection the
        execution engine changes.

            map: map executes the all scenarios in series and might take longer to run.

            process_map: executes the scenarios in parallel, but not all computers support parallel processing.

            thread_map: executes the scenarios in a threaded manner, but not all computers support parallel
            processing.

    :param verbose: a flag spefifying if debugging should be enabled.

    '''
    setup_logging(logging.INFO if not verbose else logging.DEBUG)
    _logger.info(f'Debugging level set to {logging.INFO if not verbose else logging.DEBUG}')

    _logger.info(f'Loading assumptions ({assumptions=}).')
    assumptions = Assumptions.from_file(url=assumptions)

    _logger.info(f'Loading macroeconomic scenarios ({scenarios=}).')
    scenarios = Scenarios.from_file(url=scenarios)

    _logger.info(f'Loading account level data ({account_data=}).')
    account_data = AccountData.from_file(url=account_data)

    _logger.info('Starting calculations.')
    results = Executor(method=method).execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios
    )

    _logger.info(f'Saving results ({outfile=}).')
    results.save(outfile)

    _logger.info("Done.")


if __name__ == "__main__":
    app()
