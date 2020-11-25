from pandas import read_csv, read_excel, concat, Int64Dtype, DataFrame
from datetime import datetime
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map, process_map
from .account import Account
from .assumptions import Assumptions
from .scenarios import Scenarios


class AccountData:
    """
    Container to store the account level data to run the model.

    Attributes:
        DICTIONARY: data dictionary of account level data.
        FILE_TYPE_MAP: dictionary mapping the file extension to a import function.
            Only Excel (.xlsx) and CSV (.csv) are supported.
    """
    DICTIONARY = {
        'contract_id': str,
        'segment_id': int,
        'outstanding_balance': float,
        'limit': float,
        'current_arrears': float,
        'contractual_payment': float,
        'contractual_freq': int,
        'interest_rate_type': str,
        'interest_rate_freq': int,
        'fixed_rate': float,
        'spread': float,
        'origination_date': datetime,
        'maturity_date': datetime,
        'reporting_date': datetime,
        'collateral_value': float,
        'origination_rating': int,
        'current_rating': int,
        'stage': Int64Dtype()
    }
    FILE_TYPE_MAP = {
        'XLSX': read_excel,
        'CSV': read_csv
    }

    def __init__(self, data: DataFrame):
        self.data = data

    def __len__(self):
        return len(self.data.index)

    @staticmethod
    def file_extension(url: str):
        """
        Get the file extension from the `url`

        Args:
             url: the filepath.

        Returns:
            str: the file extension (excl. the '.') in upper case.
        """
        return url.split('.')[-1].upper()

    @classmethod
    def from_file(cls, url: str):
        """
        Create an `AccountData` object from an Excel or CSV file.

        Args:
             url: relative path to the file
        """
        data = cls.FILE_TYPE_MAP[cls.file_extension(url=url)](io=url, dtype=cls.DICTIONARY, index_col='contract_id', usecols=cls.DICTIONARY.keys())
        return cls(data=data)

    @staticmethod
    def _run_scenario(args):
        name, scenario, assumptions, data = args
        results = []
        for contract_id, d in tqdm(data.iterrows(), desc=f'Model (Scenario: {name})', total=len(data.index), leave=False, position=1):
            d['assumptions'] = assumptions[d['segment_id']]
            d['scenario'] = scenario
            r = Account(**d).results.assign(**{'contract_id': contract_id, 'scenario': name})
            results.append(r)
        return concat(results)

    def execute(self, assumptions: Assumptions, scenarios: Scenarios, method='map'):
        """
        Execute the Z-model on the account level data.

        Args:
            assumptions: an :obj:`Assumptions` object containing the model assumptions for each segment.
            scenarios: an "obj:`Scenarios` object containing the economic scenarios to run.
            method: an execution method (Default: map). Should be one of the following:
                * map: use the built in `map` function.
                * thread_map: use `tqdm.contrib.concurrent.thead_map` to execute the scenarios in multiple threads.
                * process_map: use `tqdm.contrib.concurrent.process_map` to execute the scenarios in multiple processes.
                    Note that `process_map` does not support executing the model in interactive mode.

        Returns:
             A :obj:`DataFrame` with the account level ECL and ST results for each month until maturity.
        """
        args = [(n, s, assumptions, self.data) for n, s in scenarios.items()]
        r = {
            'MAP': lambda fn, x, **k: list(map(fn, tqdm(x, **k))),
            'THREAD_MAP': thread_map,
            'PROCESS_MAP': process_map,
        }.get(method.upper())(self._run_scenario, args, desc='Scenarios', position=0)
        return concat(r)
