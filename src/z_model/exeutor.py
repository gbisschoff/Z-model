from pandas import concat, merge
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map, process_map
from enum import Enum
from .account import Account, AccountData
from .assumptions import Assumptions
from .scenarios import Scenarios
from .results import Results
from .ecl_model import ECLModel


class Methods(str, Enum):
    """
    Methods

    Specifies different execution methods:

    * ``MAP``: One scenario at a time. This takes the longest to run, but is typically the most robust. This method
        has to be used if the model is executed in an interactive session.
    * ``THREAD_MAP``: Each scenario is executed in its own thread. It only provides an increase in performance for IO
        bound operations.
    * ``PROCESS_MAP``: Each scenario is executed in parallel in its own worker. This provides true parallel processing.
        This only works in non-interactive sessions, i.e. via the terminal.

    """
    Map = 'map'
    ProgressMap = 'process_map'
    ThreadMap = 'thread_map'

    def executor(self, *args, **kwargs):
        return {
            Methods.Map: lambda fn, x, **k: list(map(fn, tqdm(x, **k))),
            Methods.ThreadMap: thread_map,
            Methods.ProgressMap: process_map,
        }.get(self)(*args, **kwargs)


class Executor:
    """
    Executor

    A class used to set up and execute multiple economic scenarios. Uses :class:`Methods` to specify the execution
    method.

    """

    def __init__(self, method: Methods = Methods.Map):
        self.method = method

    @staticmethod
    def _run_scenario(args):
        """
        Execute a single macroeconomic scenario

        :param args: Tuple(name, scenario, assumptions, account_data)
        """
        name, scenario, assumptions, account_data = args
        ecl_models = {
            segment_id: ECLModel.from_assumptions(
                segment_assumptions=assumptions,
                scenario=scenario
            )
            for segment_id, assumptions in assumptions.items()
        }

        data = account_data.data.reset_index()
        data['Account()'] = data.apply(lambda x: Account(**x), axis=1)
        data['ECLModel()'] = data['segment_id'].map(ecl_models)
        data['ECL()'] = data.apply(lambda x: x['ECLModel()'][x['Account()']], axis=1)
        rs = concat(data['ECL()'].values)
        rs['scenario'] = name
        return rs

    def execute(self, account_data: AccountData, assumptions: Assumptions, scenarios: Scenarios):
        """
        Execute the Z-model on the account level data.

        :param account_data: and :class:`AccountData` object.
        :param assumptions: an :class:`Assumptions` object containing the model assumptions for each segment.
        :param scenarios: an :class:`Scenarios` object containing the economic scenarios to run.

        :return:  A :class:`Results` with the account level ECL and ST results for each month until maturity.
        """
        args = [(n, s, assumptions, account_data) for n, s in scenarios.items()]
        r = self.method.executor(self._run_scenario, args, desc='Scenarios', position=0)

        #Calculate weighted scenario
        r = concat(r).reset_index().set_index(['contract_id', 'T', 'forecast_reporting_date'])
        weights = scenarios.weights
        rw = sum([d.drop(columns='scenario') * weights.get(n) for n, d in r.groupby('scenario')])
        rw['scenario'] = 'Weighted'
        rc = concat([r, rw]).reset_index()

        return Results(merge(account_data.data, rc, how='left', on='contract_id'))
