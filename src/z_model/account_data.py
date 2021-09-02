from pandas import read_csv, read_excel, Int64Dtype, DataFrame
from datetime import datetime
from pathlib import Path


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
        'watchlist': Int64Dtype()
    }
    FILE_TYPE_MAP = {
        '.XLSX': read_excel,
        '.CSV': read_csv
    }

    def __init__(self, data: DataFrame):
        self.data = data

    def __len__(self):
        return len(self.data.index)

    @staticmethod
    def file_extension(url: Path):
        """
        Get the file extension from the `url`

        Args:
             url: the filepath.

        Returns:
            str: the file extension (excl. the '.') in upper case.
        """
        return url.suffix.upper()

    @classmethod
    def from_file(cls, url: Path):
        """
        Create an `AccountData` object from an Excel or CSV file.

        Args:
             url: relative path to the file
        """
        data = cls.FILE_TYPE_MAP[cls.file_extension(url=url)](io=url, dtype=cls.DICTIONARY, index_col='contract_id')
        return cls(data=data)
