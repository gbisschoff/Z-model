import pandas as pd
import numpy as np
from datetime import datetime
from numpy import array, zeros, sum, diag_indices_from

import seaborn as sns
import matplotlib.pyplot as plt

from .Account import Assumptions, Account, RandomSeries, Scenario

HPI = RandomSeries(theta=100).generate(140)
CCI = RandomSeries(m1=0.04, m2=0.04).generate(140)
Z = (CCI - CCI.mean())/CCI.std()
BOE = RandomSeries(theta=0.1, sigma=0, m1=0.01, m2=0.01).generate(140)

scenario = Scenario(pd.DataFrame({'HPI':HPI, 'CCI': CCI, 'Z.S [CYCICAL]':Z, 'BOE':BOE}, index=pd.date_range('2021-01-01', periods=140, freq='m')))


stage_map = {
    0: ([0, 1], [2, 3], [4], [5]),
    1: ([0, 1], [2, 3], [4], [5]),
    2: ([0, 1, 2], [3], [4], [5]),
    3: ([0, 1, 2], [3], [4], [5])
}
assumptions = Assumptions.from_file('./data/ASSUMPTIONS 2019-03-31 v2.xlsx', stage_map=stage_map)
account = Account(
        assumptions=assumptions[1],
        scenario=scenario,
        outstanding_balance=100,
        current_arrears=0,
        contractual_payment=10,
        contractual_freq=12,
        interest_rate_type='fixed',
        interest_rate_freq=12,
        spread=0.1,
        origination_date=datetime.strptime('2016-01-01', '%Y-%m-%d'),
        maturity_date=datetime.strptime('2026-01-01', '%Y-%m-%d'),
        reporting_date=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        collateral_value=20,
        origination_rating=0,
        current_rating=0
    )
account.results

scenarios = Scenarios.from_file(url='./data/SCENARIOS 2019-03-31.xlsx')
data = AccountData.from_file(url='./data/account_level_data.xlsx')
results = data.execute(
    assumptions=assumptions,
    scenarios=scenarios
)
results.to_excel('./data/results.xlsx')
