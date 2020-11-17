from pandas import read_csv, read_excel, concat
from datetime import datetime
from tqdm.auto import tqdm
from .account import Account
from .assumptions import Assumptions
from .scenarios import Scenarios


class AccountData:
    DICTIONARY = {
        'contract_id': str,
        'segment_id': int,
        'outstanding_balance': float,
        'current_arrears': float,
        'contractual_payment': float,
        'contractual_freq': int,
        'interest_rate_type': str,
        'interest_rate_freq': int,
        'spread': float,
        'origination_date': datetime,
        'maturity_date': datetime,
        'reporting_date': datetime,
        'collateral_value': float,
        'origination_rating': int,
        'current_rating': int
    }
    FILE_TYPE_MAP = {
        'XLSX': read_excel,
        'CSV': read_csv
    }

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data.index)

    @staticmethod
    def file_extension(url: str):
        return url.split('.')[-1].upper()

    @classmethod
    def from_file(cls, url):
        data = cls.FILE_TYPE_MAP[cls.file_extension(url=url)](io=url, dtype=cls.DICTIONARY, index_col='contract_id', usecols=cls.DICTIONARY.keys())
        return cls(data=data)

    def execute(self, assumptions: Assumptions, scenarios: Scenarios):
        def run_scenario(args):
            name, scenario, assumptions, data = args
            results = []
            for contract_id, d in tqdm(data.iterrows(), desc=f'Model (Scenario: {name})', total=len(data.index)):
                d['assumptions'] = assumptions[d['segment_id']]
                d['scenario'] = scenario
                r = Account(**d).results.assign(**{'contract_id': contract_id, 'scenario': name})
                results.append(r)
            return concat(results)

        args = [(n, s, assumptions, self.data) for n, s in scenarios.items()]
        r = map(run_scenario, args) #thread_map(run_scenario, args, desc='Scenario')
        return concat(r)
