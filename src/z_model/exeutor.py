from pandas import concat, merge
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map, process_map
from .account import Account
from .assumptions import Assumptions
from .scenarios import Scenarios
from .account_data import AccountData
from .results import Results


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
        results = []
        for contract_id, d in tqdm(account_data.data.iterrows(), desc=f'Model (Scenario: {name})', total=len(account_data.data.index), leave=False, position=1):
            d['assumptions'] = assumptions[d['segment_id']]
            d['scenario'] = scenario
            r = Account(**d).results.assign(**{'contract_id': contract_id, 'scenario': name})
            results.append(r)
        return concat(results)

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
        return Results(merge(account_data.data, concat(r), how='left', on='contract_id'))
