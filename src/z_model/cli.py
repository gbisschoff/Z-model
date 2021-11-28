# -*- coding: utf-8 -*-
"""
This is a CLI that can serve as a starting point for the Z-model.
To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         z_model = z_model.skeleton:run

Then run `python setup.py install` which will install the command `z_model`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.
"""

import typer
from typing import Optional
import sys
import logging
from enum import Enum
from pathlib import Path

from z_model import __version__
from z_model.assumptions import Assumptions
from z_model.scenarios import Scenarios
from z_model.account_data import AccountData
from z_model.exeutor import Executor
from .file_reader import write_file

__author__ = "Geyer Bisschoff"
__copyright__ = "Geyer Bisschoff"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

app = typer.Typer()

class Methods(str, Enum):
    Map = 'map'
    ProgressMap = 'process_map'
    ThreadMap = 'thread_map'

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


@app.command()
def about():
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
def run(
        account_data: Path,
        assumptions: Path,
        scenarios: Path,
        outfile: Path,
        detailed_output: Optional[Path] = None,
        parameter_output: Optional[Path] = None,
        monte_carlo: Optional[Path] = None,
        method: Methods = Methods.Map,
        verbose: bool = False
):
    '''
    Run the Z-model on specified inputs.

    Arguments:

    account_data (Path): path to the account level data file.
    The file should be one of the supported file types.

    assumptions (Path): path to the assumptions file.
    The file should be in .XLSX format.

    scenarios (Path): the path to the macroeconomic scenarios or monte-carlo assumptions.
    The file should be in .XLSX format. If monte-carlo assumptions are provided the --monte-carlo option should be
    used.

    outfile (Path): the path to the output file. Any standard Python Pandas file extension is supported.
    However, it is recommended to use a compressed CSV file (.csv.gz).

    detailed_output (Path): a path where the detailed forecasted results should be exported too.
    This creates a very large file containing the parameters and marginal ECLs for each forecast horizon.
    It is mainly used for debugging purposes. It is recommended to use a compressed CSV file (.csv.gz)

    parameter_output (Path): a path where the parameters should be exported too.
    It is recommended to use a compressed CSV file (.csv.gz)

    monte_carlo (Path): a flag specifying that the SCENARIOS inputs are monte-carlo assumptions and not discrete
    scenarios. A path should be provided where the generated scenarios are saved. Depending on the number of scenarios
    generated the file might become large. It is recommended to use a compressed CSV file (.csv.gz)

    method (Methods): one of either 'map', 'process_map' or 'thread_map'. Depending on the selection the
    execution engine changes.

        map: map executes the all scenarios in series and might take longer to run.

        process_map: executes the scenarios in parallel, but not all computers support parallel processing.

        thread_map: executes the scenarios in a threaded manner, but not all computers support parallel
        processing.

    verbose (bool): a flag spefifying if debugging should be enabled.
    '''
    setup_logging(logging.INFO if not verbose else logging.DEBUG)
    _logger.info(f'Debugging level set to {logging.INFO if not verbose else logging.DEBUG}')

    _logger.info(f'Loading assumptions ({assumptions=}).')
    assumptions = Assumptions.from_file(url=assumptions)
    if monte_carlo:
        _logger.info(f'Generating scenarios from monte-carlo assumptions ({scenarios=}).')
        scenarios = Scenarios.from_assumptions(url=scenarios)
        _logger.info(f'Saving monte-carlo scenarios ({monte_carlo=}).')
        scenarios.as_dataframe().to_csv(monte_carlo)
    else:
        _logger.info(f'Loading discrete scenarios ({scenarios=}).')
        scenarios = Scenarios.from_file(url=scenarios)

    _logger.info(f'Loading account level data ({account_data=}).')
    account_data = AccountData.from_file(url=account_data)

    _logger.info('Starting calculations.')
    results = Executor(method=method).execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios
    )

    if detailed_output:
        _logger.info(f'Exporting detailed results ({detailed_output=}).')
        write_file(results.data.reset_index(), detailed_output, index=False)

    _logger.info(f'Exporting summarised results ({outfile=}).')
    write_file(
        results.summarise(by=['segment_id', 'forecast_reporting_date', 'scenario']),
        outfile,
        index=False
    )

    if parameter_output:
        _logger.info(f'Exporting parameters ({parameter_output=}).')
        write_file(
            results.parameters(by=['segment_id', 'forecast_reporting_date', 'scenario']),
            parameter_output,
            index=False
        )

    _logger.info("Done.")


if __name__ == "__main__":
    app()
