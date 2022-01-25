import typer
import multiprocessing
from typing import Optional
from pathlib import Path
from datetime import datetime

from z_model import __version__
from z_model.logging import configure_logger, logger
from z_model.exeutor import Methods
from z_model.license import License

__author__ = "Geyer Bisschoff"
__copyright__ = "Deloitte LLP"
__license__ = "Proprietary Software License"

app = typer.Typer()
license = License.load(Path().home() / '.z_model_license')

@app.command()
def about():
    '''
    Print Z-model about information.
    '''
    try:
        is_valid = license.is_valid()
    except Exception as e:
        is_valid = str(e)

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
    Validity: {is_valid}
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
    try:
        if license.is_valid():
            from z_model.scenarios import Scenarios
            from z_model.file_reader import write_file

            configure_logger(verbose)
            logger.info(f'Debugging level set to {verbose=}')

            logger.info(f'Generating scenarios from monte-carlo assumptions ({assumptions=}).')
            scenarios = Scenarios.from_assumptions(url=assumptions)
            logger.info(f'Saving monte-carlo scenarios ({outfile=}).')
            write_file(
                df=scenarios.as_dataframe(),
                url=outfile
            )
            logger.info("Done.")

    except Exception as e:
        logger.error(e, exc_info=True)


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

    :param method: one of either 'map', 'process_map' or 'thread_map'. Depending on the selection the
        execution engine changes.

            map: map executes the all scenarios in series and might take longer to run.

            process_map: executes the scenarios in parallel, but not all computers support parallel processing.

            thread_map: executes the scenarios in a threaded manner, but not all computers support parallel
            processing.

    :param verbose: a flag spefifying if debugging should be enabled.

    '''
    try:
        if license.is_valid():
            from z_model.assumptions import Assumptions
            from z_model.scenarios import Scenarios
            from z_model.account import AccountData
            from z_model.exeutor import Executor
            from z_model.file_reader import write_file

            configure_logger(verbose)
            logger.info(f'Debugging level set to {verbose=}')

            logger.info(f'Loading assumptions ({assumptions=}).')
            assumptions = Assumptions.from_file(url=assumptions)

            logger.info(f'Loading macroeconomic scenarios ({scenarios=}).')
            scenarios = Scenarios.from_file(url=scenarios)

            logger.info(f'Loading account level data ({account_data=}).')
            account_data = AccountData.from_file(url=account_data)

            logger.info('Starting calculations.')
            results = Executor(method=method).execute(
                account_data=account_data,
                assumptions=assumptions,
                scenarios=scenarios
            )

            logger.info(f'Saving results ({outfile=}).')
            results.save(outfile)

            logger.info("Done.")

    except Exception as e:
        logger.error(e, exc_info=True)

@app.command(hidden=True)
def create_license(
        sign_key: Path,
        outfile: Path,
        verbose: bool = False,
        company_name: str = typer.Option(..., prompt=True),
        email: str = typer.Option(..., prompt=True),
        expiration_date: datetime = typer.Option(..., prompt=True, formats=['%Y-%m-%d'])
):
    '''
    Create a use license and save to file.

    :param company_name: The company the license is for.

    :param email: The user's email address.

    :param expiration_date: The expiration date of the license.

    :param sign_key: The location of the private key used to sign licenses.

    :param outfile: The location where the license should be saved.

    '''
    try:
        from z_model.cryptography import PrivateKey
        from z_model.license import create_license
        configure_logger(verbose)
        logger.info(f'Loading sign-key. ({sign_key=})')
        sign_key = PrivateKey.load(sign_key)
        logger.info(f'Creating license. ({company_name=}, {email=}, {expiration_date=})')
        l = create_license(company_name, email, expiration_date.strftime(format='%Y-%m-%d'), sign_key)
        logger.info(f'Saving license. {outfile=}')
        l.save(outfile)
    except Exception as e:
        logger.error(e, exc_info=True)

def main():
    multiprocessing.freeze_support()
    app()

if __name__ == "__main__":
    main()