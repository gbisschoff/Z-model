import typer
import multiprocessing
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from z_model import __version__
from z_model.exeutor import Methods
from z_model.license import License
from z_model.logging import logging, setup_logging
from z_model.climate_risk_scenarios import ClimateRiskScenarios
from z_model.forecast import ForecastType, forecast

setup_logging()
__author__ = "Geyer Bisschoff"
__copyright__ = "Deloitte LLP"
__license__ = "Proprietary Software License"

logging.info(f'Logging setup.')
app = typer.Typer()

try:
    license = License.load(Path().home() / '.z_model_license')
except Exception as e:
    logging.error(
        f"User license error. Please check that the user license is saved at the correct location.\n"
        f"The software expects the license file to be named and located in (Windows) C:/Users/%USERNAME%/.z_model_license\n"
        f"{e}"
    )


@app.command()
def about():
    """
    Print Z-model about information.
    """

    return typer.echo(
    f"""
    Z-Model
    =========================
    Version: {__version__}
    Copyright: {__copyright__}
    License: {__license__}
    Author: {__author__}
    
    User License Information:
    =========================
    Company Name: {license.information.get('company_name', 'unknown')}
    Email: {license.information.get('email', 'unknown')}
    Expiration Date: {license.information.get('expiration_date', 'unknown')}
    Product Code: {license.signature}
    Validity: {license.is_valid()}
    """
    )


@app.command()
def generate_scenarios(
    assumptions: Path,
    outfile: Path
):
    """
    Generate macroeconomic scenarios using Monte Carlo

    :param assumptions: the path to the MONTE_CARLO_ASSUMPTIONS.xlsx file.
    :param outfile: the path to save the generated scenarios. Recommended to be a .xlsx file forecast_type.

    """
    try:
        if license.is_valid():
            from z_model.scenarios import Scenarios
            from z_model.file_reader import write_file

            logging.info(f'Generating scenarios from monte-carlo assumptions ({assumptions=}).')
            scenarios = Scenarios.from_assumptions(url=assumptions)
            logging.info(f'Saving monte-carlo scenarios ({outfile=}).')
            scenarios.to_file(url=outfile)
            logging.info("Done.")

    except Exception as e:
        logging.error(e)
        raise Exception(e)


@app.command()
def run(
        forecast_type: ForecastType,
        account_data: Path,
        assumptions: Path,
        scenarios: Path,
        outfile: Path,
        by: Optional[List[str]] = ('segment_id', ),
        portfolio_assumptions: Optional[Path] = None,
        climate_risk_scenarios: Optional[Path] = None,
        start: Optional[int] = 0,
        stop: Optional[int] = 60,
        step: Optional[int] = 12,
        method: Methods = Methods.Map
):
    """
    Run the Z-model on specified inputs.

    :param forecast_type: the type of forecast to do.

    :param account_data: path to the account level data file.
        The file should be one of the supported file types.

    :param assumptions: path to the assumptions file.
        The file should be in .XLSX format.

    :param scenarios: the path to the macroeconomic scenarios.
        The file should be in .XLSX, .CSV or .CSV.GZ format.

    :param outfile: the path to the output file. Results are stored in a zip archive and thus should have the
        a `.zip` extension.

    :param method: one of either 'map', 'process_map' or 'thread_map'. Depending on the selection the
        execution engine changes.

            map: map executes the all scenarios in series and might take longer to run.

            process_map: executes the scenarios in parallel, but not all computers support parallel processing.

            thread_map: executes the scenarios in a threaded manner, but not all computers support parallel
            processing.

    :param by: a field in the data to summarise by. Multiple `--by` arguments may be passed.

    :param portfolio_assumptions: the path to the portfolio assumptions input file. This file contains data about
        the forecast portfolio and is used to generate simulated accounts matching the characteristics. The type of
        account can be accessed via the `account_type` variable (this can be passed in a `--by` statement).

    :param climate_risk_scenarios: the path to the climate risk scenarios template. This file contains data about
        the climate risk value adjustments applied to the LGD model.

    :param start: Used for dynamic balance sheet forecasting.The initial offset in months. (default = 0 months)

    :param stop: Used for dynamic balance sheet forecasting. The maximum offset in months. (default = 60 months)

    :param step: Used for dynamic balance sheet forecasting. The offset step size in months. (default = 12 months)

    """
    try:
        if license.is_valid():
            from z_model.assumptions import Assumptions
            from z_model.scenarios import Scenarios
            from z_model.account import AccountData, SimulatedAccountData
            from z_model.exeutor import Executor
            from z_model.file_reader import write_file

            logging.info(f'Loading assumptions ({assumptions=}).')
            assumptions = Assumptions.from_file(url=assumptions)

            logging.info(f'Loading macroeconomic scenarios ({scenarios=}).')
            scenarios = Scenarios.from_file(url=scenarios)

            logging.info(f'Loading account level data ({account_data=}).')
            account_data = AccountData.from_file(url=account_data)

            simulated_accounts = None
            if portfolio_assumptions:
                logging.info(f'Loading business assumptions ({portfolio_assumptions=}).')
                simulated_accounts = SimulatedAccountData.from_file(portfolio_assumptions)

            climate_risk_scenarios_data = None
            if climate_risk_scenarios:
                logging.info(f'Loading business assumptions ({climate_risk_scenarios=}).')
                climate_risk_scenarios_data = ClimateRiskScenarios.from_file(climate_risk_scenarios)

            logging.info('Starting calculations.')
            results = forecast(
                forecast_type=forecast_type,
                method=method,
                account_data=account_data,
                assumptions=assumptions,
                scenarios=scenarios,
                simulated_accounts=simulated_accounts,
                climate_risk_scenarios=climate_risk_scenarios_data,
                start=start,
                stop=stop,
                step=step
            )

            logging.info(f'Saving results ({outfile=}) ({by=}).')
            by = [*by, 'reporting_date', 'forecast_reporting_date', 'scenario']
            results.save(outfile, by=by)

            logging.info("Done.")

    except Exception as e:
        logging.error(e)
        raise Exception(e)


@app.command(hidden=True)
def create_license(
        sign_key: Path,
        outfile: Path,
        company_name: str = typer.Option(..., prompt=True),
        email: str = typer.Option(..., prompt=True),
        expiration_date: datetime = typer.Option(..., prompt=True, formats=['%Y-%m-%d'])
):
    """
    Create a use license and save to file.

    :param company_name: The company the license is for.

    :param email: The user's email address.

    :param expiration_date: The expiration date of the license.

    :param sign_key: The location of the private key used to sign licenses.

    :param outfile: The location where the license should be saved.

    """
    try:
        from z_model.cryptography import PrivateKey
        from z_model.license import create_license
        logging.info(f'Loading sign-key. ({sign_key=})')
        sign_key = PrivateKey.load(sign_key)
        logging.info(f'Creating license. ({company_name=}, {email=}, {expiration_date=})')
        l = create_license(company_name, email, expiration_date.strftime(format='%Y-%m-%d'), sign_key)
        logging.info(f'Saving license. {outfile=}')
        l.save(outfile)
    except Exception as e:
        logging.error(e)
        raise Exception(e)


@app.command()
def gui():
    """
    Launch the Z-Model graphical user interface.
    """
    from z_model.__gui__ import main
    main()


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    """
    Z-Model entry point
    """
    if ctx.invoked_subcommand is None:
        gui()


def main():
    multiprocessing.freeze_support()
    app()


if __name__ == "__main__":
    main()
