"""
This example shows how to run the IFRS9 and Stress Testing model on a set of accounts.

Steps to run the model:
1. configure the model assumptions in the ASSUMPTIONS.xlsx template
2. configure the economic scenarios (either Monte Carlo or Defined) using the appropriate template
3. ensure the account level data adheres to the data template
4. configure the run script below to execute the model:
    Decide on an execution method. It can be one of the following:
    - MAP: Use the built in `map` function of Python. This runs all scenarios in series, so might be a bit slow, but
        it should also be the most reliable and give the least amount of issues.
    - THREAD_MAP: Use tqdm's thread_map function to execute the model in parallel over multiple threads, it might be
        a bit faster, but might cause some issues.
    - PROCESS_MAP: Use tqdm's process_map function to execute the model in full parallel mode over multiple processes.
        This is the fastest method to run the model, but can't be run in interactive mode (i.e. run it from the
        terminal using the command `py main.py`. It also requires the `if __name__ == '__main__':` piece of code).
        It requires the most effort to set it up, but once you get the model to start running it should run the fastest.
        This method is recommended for projects which requires multiple runs.

"""
from pathlib import Path
from z_model.assumptions import Assumptions
from z_model.scenarios import Scenarios
from z_model.account_data import AccountData
from z_model.exeutor import Executor

if __name__ == '__main__':

    assumptions = Assumptions.from_file(url=Path('./data/ASSUMPTIONS.xlsx'))
    scenarios = Scenarios.from_file(url=Path('./data/SCENARIOS.xlsx'))
    account_data = AccountData.from_file(url=Path('./data/account_level_data.xlsx'))

    results = Executor(method='process_map').execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios
    )

    print(results.summarise().loc[0])
    results.summarise(by=['segment_id', 'forecast_reporting_date', 'scenario', 'Stage']) \
        .reset_index() \
        .to_csv(Path('./data/results.csv.gz'), index=False)
