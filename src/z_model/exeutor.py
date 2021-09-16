from pandas import concat, merge
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map, process_map
from .account import Account
from .assumptions import Assumptions
from .scenarios import Scenarios
from .account_data import AccountData
from .results import Results
from .ecl_model import ECLModel


class Executor:
    METHODS = {
        'MAP': lambda fn, x, **k: list(map(fn, tqdm(x, **k))),
        'THREAD_MAP': thread_map,
        'PROCESS_MAP': process_map,
    }

    def __init__(self, method: str):
        self.method = method.upper()

    @staticmethod
    def _run_scenario(args):
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

        Args:
            account_data: and `AccountData` object.
            assumptions: an :obj:`Assumptions` object containing the model assumptions for each segment.
            scenarios: an "obj:`Scenarios` object containing the economic scenarios to run.

        Returns:
             A :obj:`Results` with the account level ECL and ST results for each month until maturity.
        """
        args = [(n, s, assumptions, account_data) for n, s in scenarios.items()]
        r = self.METHODS.get(self.method)(self._run_scenario, args, desc='Scenarios', position=0)
        return Results(merge(account_data.data, concat(r).reset_index(), how='left', on='contract_id'))
