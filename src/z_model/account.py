from numpy import array, zeros, isnat
from pandas import date_range, period_range, Int64Dtype, DataFrame, isnull
from dateutil.relativedelta import relativedelta
from datetime import datetime
from pathlib import Path
from .file_reader import read_file


class Account:
    '''
    Account

    Each row in the :class:`AccountData` gets converted into an :class:`Account` object with the same properties.
    Two additional properties are added to the account as calculated fields. These are:

    * time_on_book: the difference in months betweent the origination date and reporting date.
    * remaining_life_index: a :class:`date_range` object specifying the date index between the reporting date and the
      end of the accounts remaining life.

    '''
    def __init__(self, contract_id: str, outstanding_balance:float, limit:float, current_arrears:float, contractual_payment:float, contractual_freq:int, interest_rate_type:str, interest_rate_freq:int, fixed_rate:float, spread:float, origination_date:datetime, payment_holiday_end_date:datetime, maturity_date:datetime, reporting_date:datetime, remaining_life:int, collateral_value:float, origination_rating:int, current_rating:int, watchlist:int, *args, **kwargs):
        self.contract_id = contract_id
        self.outstanding_balance = outstanding_balance
        self.limit = limit
        self.current_arrears = current_arrears
        self.interest_rate_type = interest_rate_type
        self.interest_rate_freq = interest_rate_freq
        self.fixed_rate = fixed_rate
        self.spread = spread
        self.origination_date = origination_date
        self.payment_holiday_end_date = payment_holiday_end_date
        self.maturity_date = maturity_date
        self.reporting_date = reporting_date
        self.remaining_life = remaining_life
        self.collateral_value = collateral_value
        self.contractual_payment = contractual_payment
        self.contractual_freq = contractual_freq
        self.origination_rating = origination_rating
        self.current_rating = current_rating
        self.watchlist = watchlist
        self.time_on_book = (reporting_date.year - origination_date.year) * 12 + \
               (reporting_date.month - origination_date.month)
        self.remaining_life_index = date_range(reporting_date, periods=remaining_life, freq='M')


class AccountData:
    """
    Account Data.

    The data dictionary of account level data. The data should contain the following attributes:

    * contract_id (String): contract unique identifier.

    * segment_id (Integer): segmentation ID used to look up the segment assumptions from the :class:`Assumptions`.

    * outstanding_balance (Double): The outstanding principle and interest at the reporing date.

    * limit (Double): The credit limit of the contract. It is only used if the `CCF` method is selected to model
      :class:`ExposureAtDefault`.

    * current_arrears (Double): The overdue principle and interest at the reporting date.

    * contractual_payment (Double): The contractual principle and interest payment.

    * contractual_freq (Integer): The number of contractual payments made per year.
      For monthly repayments use the value 12.

    * interest_rate_type (String): The interest rate type, either `FIXED` or `FLOATING`. If the interest rate type
      is set to `FIXED` the `fixed_rate` column should be populated. If the interest rate type is set to
      `FLOATING` the `spread` column should be populated.

    * interest_rate_freq (Integer): The interest rate compounding frequency. In most cases this would be annually,
      in which case it should be set to 1, if compounded monthly it should be 12.

    * fixed_rate (Double): The fixed interest rate.

    * spread (Double): The floating interest rate excluding the base rate.

    * origination_date (Date: YYYY-MM-DD): The contract origination date.

    * payment_holiday_end_date (Date: YYYY-MM-DD): The date the payment holiday ends. If the end date is on the same
      date when the next payment is due, it is assumed that the payment is required on that date.

    * reporting_date (Date: YYYY-MM-DD): The current reporting date. The model also supports running future and
      past reporting dates. Future reporting dates could be used to run business grow and ICAAP stress testing
      forecasts.

    * remaining_life (Integer): The remaining behavioural life for the contract. This is the number of periods
      considered in the ECL formula. The value should be greater than zero.

    * collateral_value (Double): The value of security held against the contract. If unsecured set as zero.

    * origination_rating (Integer): The risk rating at origination. It should match one of the ratings in the
      :class:`TransitionMatrix`. It should be a value from 1 - N, where 1 is the best rating and N is the worst.

    * current_rating (Integer): The risk rating at reporting date.

    * watchlist (Integer): Watchlist number (between 1 and 3) used to force an account into a specific Stage for
      a period of time. The default should be missing, which means that the IFRS9 Stage will be determined by the
      `origination_rating`, `current_rating` and the :class:`StageMap`.

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
        'payment_holiday_end_date': datetime,
        'reporting_date': datetime,
        'remaining_life': int,
        'collateral_value': float,
        'origination_rating': int,
        'current_rating': int,
        'watchlist': Int64Dtype()
    }

    def __init__(self, data: DataFrame):
        '''
        Create an `AccountData` object from a Pandas DataFrame.
        '''
        self.data = data

    def __len__(self):
        '''
        Return the number of accounts in the data.
        '''
        return len(self.data.index)

    @classmethod
    def from_file(cls, url: Path):
        """
        Create an `AccountData` object from a file.

        :param url: relative path to the file containing account data.
            The account data should contain the columns as specified by the `DICTIONARY` attribute.
            The function support file formats as specified by the `file_reader` module.
        """
        data = read_file(url=url, dtype=cls.DICTIONARY, index_col='contract_id')
        return cls(data=data)
