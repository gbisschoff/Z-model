from numpy import array, zeros
from pandas import date_range, period_range
from dateutil.relativedelta import relativedelta


class Account:
    def __init__(self, contract_id: str, outstanding_balance, current_arrears, contractual_payment, contractual_freq, interest_rate_type, interest_rate_freq, fixed_rate, spread, origination_date, maturity_date, reporting_date, remaining_life, collateral_value, origination_rating, current_rating, watchlist, *args, **kwargs):
        self.contract_id = contract_id
        self.outstanding_balance = outstanding_balance
        self.current_arrears = current_arrears
        self.interest_rate_type = interest_rate_type
        self.interest_rate_freq = interest_rate_freq
        self.fixed_rate = fixed_rate
        self.spread = spread
        self.origination_date = origination_date
        self.maturity_date = maturity_date
        self.reporting_date = reporting_date
        self.remaining_life = remaining_life
        self.collateral_value = collateral_value
        self.contractual_payment = contractual_payment
        self.contractual_freq = contractual_freq
        self.origination_rating = origination_rating
        self.current_rating = current_rating
        self.watchlist = watchlist
        self.remaining_term = (maturity_date.year - reporting_date.year) * 12 + \
               (maturity_date.month - reporting_date.month)
        self.past_maturity = maturity_date <= reporting_date
        self.time_on_book = (reporting_date.year - origination_date.year) * 12 + \
               (reporting_date.month - origination_date.month)
        self.term = (maturity_date.year - origination_date.year) * 12 + \
               (maturity_date.month - origination_date.month)
        self.remaining_life_index = date_range(reporting_date, periods=remaining_life, freq='M')