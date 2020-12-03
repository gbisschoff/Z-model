"""
This example shows how to run the IFRS9 and Stress Testing model on a set of accounts.

Steps to run the model:
1. configure the model assumptions in the ASSUMPTIONS.xlsx template
2. configure the economic scenarios (either Monte Carlo or Defined) using the appropriate template
3. ensure the account level data adheres to the data template
4. configure a stage map below. The stage map dictionary maps origination_rating and current_rating to one of the following
    states: Stage 1, Stage 2, Stage 3 or Write-off. The dictionary should be of the form:

    stage_map = {
        origination rating (int): (
            [list current ratings to map to stage 1] (list: int),
            [list current ratings to map to stage 2] (list: int),
            [list current ratings to map to stage 3] (list: int),
            [list current ratings to map to write-off] (list: int)
        ),
        ...
    }

   The ratings should match that of the configured Transition Matrix in the ASSUMPTIONS.xlsx template.
   Note that an extra state is automatically added to the transition matrix for write-off.

5. configure the run script below to execute the model:
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
from z_model.assumptions import Assumptions
from z_model.scenarios import Scenarios
from z_model.account_data import AccountData
from z_model.exeutor import Executor

if __name__ == '__main__':
    stage_map = {
        0: ([0, 1], [2, 3], [4], [5]),
        1: ([0, 1], [2, 3], [4], [5]),
        2: ([0, 1, 2], [3], [4], [5]),
        3: ([0, 1, 2], [3], [4], [5])
    }

    assumptions = Assumptions.from_file(url='./data/ASSUMPTIONS.xlsx', stage_map=stage_map)
    scenarios = Scenarios.from_file(url='./data/SCENARIOS.xlsx')
    account_data = AccountData.from_file(url='./data/account_level_data.xlsx')

    results = Executor(method='process_map').execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios
    )

    print(results.summarise().loc[0])
    results.data.to_csv('./data/results.csv', index=False)
