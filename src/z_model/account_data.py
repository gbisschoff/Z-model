from pandas import read_csv, read_excel, Int64Dtype, DataFrame
from datetime import datetime
from pathlib import Path
from .file_reader import read_file

class AccountData:
    """
    Container to store the account level data to run the model.

    Attributes:
        DICTIONARY: data dictionary of account level data.

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
        'remaining_life': int,
        'collateral_value': float,
        'origination_rating': int,
        'current_rating': int,
        'watchlist': Int64Dtype()
    }

    def __init__(self, data: DataFrame):
        self.data = data

    def __len__(self):
        return len(self.data.index)

    @classmethod
    def from_file(cls, url: Path):
        """
        Create an `AccountData` object from a file.

        Args:
             url: relative path to the file
        """
        data = read_file(url=url, dtype=cls.DICTIONARY, index_col='contract_id')
        return cls(data=data)
