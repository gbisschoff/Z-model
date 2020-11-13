from scipy.stats import norm as normal
from numpy import prod as product
from numpy import array, zeros
import pandas as pd
import numpy as np
from functools import reduce
from scipy.linalg import fractional_matrix_power
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map
from functools import lru_cache
from pylab import plot, show, xlabel, ylabel, axhline


class Series:
    def __init__(self, T:float, N:int, x0:float=None, dx0=.0, theta=.0, m1=.0, m2=.0, sigma=.0, m=1, fun=lambda x: x):
        self.T = T
        self.N = N
        self.x0 = theta if x0 is None else x0
        self.dx0 = dx0
        self.theta = theta
        self.m1 = m1
        self.m2 = m2
        self.sigma = sigma
        self.m=m
        self.fun=fun
        self.dt = T / N
        self.dx, self.x, self.fx = self._forecast()

    def __getitem__(self, item):
        return self.__dict__[item]

    def _forecast(self):
        x = np.empty((self.m, self.N+1)); x[:,0] = self.x0
        dx = np.empty((self.m, self.N+1)); dx[:,0] = self.dx0
        dw = np.random.normal(scale=np.sqrt(self.dt), size=(self.m, self.N))

        for i in range(self.N):
            dx[:,i+1] = self.m1*(self.theta-x[:,i]) * self.dt + self.m2*dx[:,i] + self.sigma * dw[:,i]
            x[:,i + 1] = x[:,i] + dx[:,i+1]

        return dx, x, self.fun(x)

    def plot(self, type='fx'):
        x = self[type]
        t = np.linspace(0.0, self.T, self.N + 1)
        for k in range(self.m):
            plot(t, x[k])
        axhline(y=self.fun(self.theta), color='black', ls='--')
        xlabel('t', fontsize=16)
        ylabel(type, fontsize=16)
        show()


class Collateral:
    def __init__(self, value: array):
        self.value = value

    def __len__(self):
        return len(self.value)

    def __getitem__(self, t):
        return self.value[t]

    @classmethod
    def from_assumptions(cls, collateral_value: float, index: array, latest_valuation_date: float = 0):
        return cls(collateral_value * index[latest_valuation_date:]/index[latest_valuation_date])


class TransitionMatrix:
    def __init__(self, transition_matrix):
        self.transition_matrix = transition_matrix

    def __len__(self):
        return len(self.transition_matrix)

    def __getitem__(self, t):
        if isinstance(t, slice):
            if t.start == t.stop:
                return np.identity(self.transition_matrix.shape[-1])
            else:
                return TransitionMatrix.matrix_cumulative_prod(self.transition_matrix[t])
        else:
            return self.transition_matrix[t]

    @staticmethod
    def matrix_cumulative_prod(l):
        return reduce(lambda a, x: a @ x if len(a) > 0 else x, l)

    @classmethod
    def from_assumption(cls, ttc_transition_matrix, rho, z, default_state=-1, freq=12, delta=10**-8):

        def fraction_matrix(x, freq):
            temp = fractional_matrix_power(x, 1 / freq)
            temp[temp < 0] = 0
            return standardise(temp)

        def standardise(x, delta=0):
            return x / (np.sum(x, axis=1, keepdims=True) * (1+delta))

        def default_distance(ttc_transition_matrix, default_state, delta):
            return -normal.ppf(ttc_transition_matrix[:, default_state] - delta)

        def default_barrier(ttc_transition_matrix, default_state, delta):
            n = len(ttc_transition_matrix)
            default_distance_vector = default_distance(ttc_transition_matrix, default_state, delta)

            default_barrier_matrix = zeros((n, n))
            for i in range(n):
                default_barrier_matrix[:, i] = normal.ppf(np.sum(ttc_transition_matrix[:, i:], axis=1) - delta) + default_distance_vector

            return default_barrier_matrix

        def z_default_distance(default_distance_vector, rho, z):
            return (default_distance_vector + rho ** 0.5 * z) / (1 - rho) ** 0.5

        def transition_matrix(default_barrier_matrix, z_dd, default_state, delta):
            n = len(default_barrier_matrix)
            matrix = zeros((n, n))

            for i in range(n - 1):
                matrix[:, i] = normal.cdf(default_barrier_matrix[:, i], z_dd) - normal.cdf(default_barrier_matrix[:, i+1], z_dd)
            matrix[:, default_state] = normal.cdf(default_barrier_matrix[:, default_state], z_dd) + delta
            return standardise(matrix)

        ttc_transition_matrix = fraction_matrix(standardise(ttc_transition_matrix, delta), freq)
        default_distance_vector = default_distance(ttc_transition_matrix, default_state, delta)
        default_barrier_matrix = default_barrier(ttc_transition_matrix, default_state, delta)
        return cls(array([
            transition_matrix(default_barrier_matrix, z_default_distance(default_distance_vector, rho, z_i), default_state, delta)
            for z_i in z
        ]))


class ProbabilityOfDefault:
    def __init__(self, probability_of_default: array):
        self.probability_of_default = probability_of_default

    def __len__(self):
        return len(self.probability_of_default)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return 1 - product(1 - self.probability_of_default[t])
        else:
            return self.probability_of_default[t]

    @classmethod
    def from_assumptions(cls, ttc: float, rho: float, z: array):
        return cls(normal.cdf((normal.ppf(ttc) - rho ** 0.5 * z) / (1-rho) ** 0.5))

    @classmethod
    def from_transition_matrix(cls, transition_matrix: TransitionMatrix, current_state: int, default_state: int = -1):
        cumulative_pd_curve = pd.Series(array([transition_matrix[0:i] for i in range(1, len(transition_matrix))])[:, current_state, default_state])
        return cls(array(((cumulative_pd_curve - cumulative_pd_curve.shift(1).fillna(0)) / (1 - cumulative_pd_curve.shift(1).fillna(0))).fillna(1)))


class Survival:
    def __init__(self, survival):
        self.survival = survival

    def __len__(self):
        return len(self.survival)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return product(self.survival[t])
        else:
            return self.survival[t]

    @classmethod
    def from_assumptions(cls, probability_of_default, redemption_rate):
        return cls(np.maximum(1 - probability_of_default - redemption_rate, 0))


class EffectiveInterestRate:
    def __init__(self, effective_interest_rate: array):
        self.effective_interest_rate = effective_interest_rate

    def __len__(self):
        return len(self.effective_interest_rate)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return product(1 + self.effective_interest_rate[t]) - 1
        else:
            return self.effective_interest_rate[t]

    @classmethod
    def from_assumptions(cls, spread: float, base_rate: array = None, frequency: int = 12):
        base_rate = zeros(35*12) if base_rate is None else base_rate
        return cls((1 + spread + base_rate) ** (1 / frequency) - 1)


class ExposureAtDefault:
    def __init__(self, exposure_at_default):
        self.exposure_at_default = exposure_at_default

    def __len__(self):
        return len(self.exposure_at_default)

    def __getitem__(self, t):
        return self.exposure_at_default[t]

    @classmethod
    def from_assumptions(cls, outstanding_balance, current_arrears, remaining_term, contractual_payment, contractual_freq, effective_interest_rate, fixed_fees=0, fees_pct=0, prepayment_pct=0):
        balance = [outstanding_balance]
        arrears = [0]
        for t in range(1, remaining_term + 1):
            pmt = contractual_payment if (remaining_term - t) % (12 / contractual_freq) == 0 else 0
            balance.append(max(balance[-1] * (1 + effective_interest_rate[t] + fees_pct - prepayment_pct) + fixed_fees - pmt, 0))
            arrears.append(max(contractual_payment * (1 - (1 + effective_interest_rate[t]) ** min(max(3 - current_arrears / contractual_payment, 1), t * contractual_freq/12)) / (1 - (1 + effective_interest_rate[t])), 0))

        balance = array(balance)
        arrears = array(arrears)
        return cls((balance + arrears)/outstanding_balance)


class LossGivenDefault:
    def __init__(self, loss_given_default):
        self.loss_given_default = loss_given_default

    def __len__(self):
        return len(self.loss_given_default)

    def __getitem__(self, t):
        return self.loss_given_default[t]

    @classmethod
    def secured_loss_given_default(cls, probability_of_cure, loss_given_cure, exposure_at_default, collateral, time_to_sale, forced_sale_discount, sales_cost, effective_interest_rate, floor):
        return cls(array([
            probability_of_cure * \
            loss_given_cure + \
            (1 - probability_of_cure) * \
            max(
                (exposure_at_default[t] - collateral[int(t + time_to_sale)] * (1 - forced_sale_discount - sales_cost) /
                 (1 + effective_interest_rate[t: int(t + time_to_sale)])) / exposure_at_default[t],
                floor
            )
            for t in range(len(exposure_at_default))
        ]))

    @classmethod
    def unsecured_loss_given_default(cls, probability_of_cure, loss_given_cure, loss_given_write_off):
        return cls(array([probability_of_cure * loss_given_cure + (1 - probability_of_cure) * loss_given_write_off] * 35 * 12))

    @classmethod
    def from_assumptions(cls, is_secured: bool, **kwargs):
        if is_secured:
            return cls.secured_loss_given_default(**kwargs)
        else:
            return cls.unsecured_loss_given_default(**kwargs)


class StageProbability:
    def __init__(self, X):
        self.X = X

    def __len__(self):
        return len(self.X)

    def __getitem__(self, t):
        return self.X[t]

    @classmethod
    def from_transition_matrix(cls, transition_matrix, origination_rating, current_rating, stage_mapping):
        cp = array([transition_matrix[0:i] for i in range(len(transition_matrix))])[:, current_rating]
        cp = array([[cp[t, stage_mapping[origination_rating][stage]].sum() for stage in range(4)] for t in range(len(cp))])
        return cls(cp)


class Model:
    def __init__(self, stage_probability, exposure_at_default, survival, probability_of_default, loss_given_default, effective_interest_rate, outstanding_balance, remaining_term, *args, **kwargs):
        self.stage_probability = stage_probability
        self.exposure_at_default = exposure_at_default
        self.survival = survival
        self.probability_of_default = probability_of_default
        self.loss_given_default = loss_given_default
        self.effective_interest_rate = effective_interest_rate
        self.remaining_term = remaining_term
        self.outstanding_balance = outstanding_balance

    @property
    def results(self):
        result = pd.DataFrame({
            'S(t)': array([self.survival[:t] for t in range(self.remaining_term)]),
            'PD(t)': array([self.probability_of_default[t] for t in range(self.remaining_term)]),
            'EAD(t+1)': array([self.exposure_at_default[t+1] for t in range(self.remaining_term)]),
            'LGD(t)': array([self.loss_given_default[t] for t in range(self.remaining_term)]),
            'LGD(t+1)': array([self.loss_given_default[t+1] for t in range(self.remaining_term)]),
            'DF(t+1)': array([1 / (1 + self.effective_interest_rate[:t+1]) for t in range(self.remaining_term)]),
            'P(S=1)': array([self.stage_probability[t, 0] for t in range(self.remaining_term)]),
            'P(S=2)': array([self.stage_probability[t, 1] for t in range(self.remaining_term)]),
            'P(S=3)': array([self.stage_probability[t, 2] for t in range(self.remaining_term)])
        }, index=range(self.remaining_term))
        result.index.name = 'T'
        result['Marginal CR(t)'] = result['S(t)'] * result['PD(t)'] * result['EAD(t+1)'] * result['LGD(t+1)'] * result['DF(t+1)']
        result['STAGE1(t)'] = (result['Marginal CR(t)'][::-1].cumsum() - result['Marginal CR(t)'][::-1].cumsum().shift(12).fillna(0)) * result['DF(t+1)'][1] / result['DF(t+1)']
        result['STAGE2(t)'] = result['Marginal CR(t)'][::-1].cumsum() * result['DF(t+1)'][1] / result['DF(t+1)']
        result['STAGE3(t)'] = result['LGD(t)']
        result['CR(t)'] = result['STAGE1(t)'] * result['P(S=1)'] + result['STAGE2(t)'] * result['P(S=2)'] + result['STAGE3(t)'] * result['P(S=3)']
        result['ECL(t)'] = result['CR(t)'] * self.outstanding_balance
        return result

    @property
    def coverage_ratio(self):
        return self.results['CR(t)']


class Assumptions:
    """
    Container that holds all the assumptions in a nested dictionary.
    """
    DICTIONARY = {
        'ASSUMPTIONS': {
            'segment_name': str,
            'segment_id': int,
            'pd_z': str,
            'pd_rho': float,
            'pd_redemption_rate': float,
            'lgd_is_secured': bool,
            'lgd_collateral_index': str,
            'lgd_probability_of_cure': float,
            'lgd_loss_given_cure': float,
            'lgd_forced_sale_discount': float,
            'lgd_sales_cost': float,
            'lgd_time_to_sale': int,
            'lgd_loss_given_write_off': float,
            'lgd_floor': float,
            'ead_fixed_fees': float,
            'ead_fees_pct': float,
            'ead_prepayment_pct': float,
            'eir_base_rate': str
        },
        'TRANSITION_MATRIX': {
            'segment_id': int,
            'from': int,
            'to': int,
            'value': float,
        }
    }

    def __init__(self, **kwargs):
        self.assumptions = kwargs

    def __getitem__(self, item):
        return self.assumptions[item]

    def __str__(self):
        return str(f'Assumptions({self["segment_name"]})')

    def __repr__(self):
        return str(self)

    @classmethod
    def from_file(cls, url, stage_map):
        assumptions = pd.read_excel(
            io=url,
            sheet_name='ASSUMPTIONS',
            dtype=cls.DICTIONARY['ASSUMPTIONS'],
            index_col='segment_id',
            usecols=cls.DICTIONARY['ASSUMPTIONS'].keys()
        )
        transition_matrixes = pd.read_excel(
            io=url,
            sheet_name='TRANSITION_MATRIX',
            dtype=cls.DICTIONARY['TRANSITION_MATRIX'],
            index_col='segment_id',
            usecols=cls.DICTIONARY['TRANSITION_MATRIX'].keys()
        )

        segments = {}
        for segment_id, dct in assumptions.iterrows():
            dct['pd_ttc_transition_matrix'] = np.array(
                transition_matrixes.loc[segment_id].pivot(index='from', columns='to', values='value'))
            dct['stage_map'] = stage_map
            segments[segment_id] = cls(**dct)

        return segments


class Scenario:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]


class Scenarios:
    def __init__(self, x: dict):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item]

    def items(self):
        return self.x.items()

    @property
    def scenarios(self):
        return list(self.x.keys())

    @classmethod
    def from_file(cls, url):
        data = pd.read_excel(
            io=url,
            sheet_name='DATA',
            dtype={
                'SCENARIO': str,
                'DATE': datetime
            },
            index_col = 'DATE'
        )

        scenarios = dict()
        for s, d in data.groupby('SCENARIO'):
            scenarios[s] = Scenario(d)

        return cls(scenarios)


class Account:
    def __init__(self, assumptions: Assumptions, scenario: Scenario, outstanding_balance, current_arrears, contractual_payment, contractual_freq, interest_rate_type, interest_rate_freq, spread, origination_date, maturity_date, reporting_date, collateral_value, origination_rating, current_rating, *args, **kwargs):
        self.assumptions = assumptions
        self.scenario = scenario
        self.outstanding_balance = outstanding_balance
        self.current_arrears = current_arrears
        self.interest_rate_type = interest_rate_type
        self.interest_rate_freq = interest_rate_freq
        self.spread = spread
        self.origination_date = origination_date
        self.maturity_date = maturity_date
        self.reporting_date = reporting_date
        self.collateral_value = collateral_value
        self.contractual_payment = contractual_payment
        self.contractual_freq = contractual_freq
        self.origination_rating = origination_rating
        self.current_rating = current_rating

    @property
    def is_secured(self):
        return self.assumptions['lgd_is_secured']

    @property
    def remaining_term(self):
        return self.term - self.time_on_book

    @property
    def time_on_book(self):
        return (self.reporting_date.year - self.origination_date.year) * 12 + \
               (self.reporting_date.month - self.origination_date.month)

    @property
    def term(self):
        return (self.maturity_date.year - self.origination_date.year) * 12 + \
               (self.maturity_date.month - self.origination_date.month)

    @property
    def collateral(self):
        if self.is_secured:
            return Collateral.from_assumptions(
                collateral_value=self.collateral_value,
                index=self.scenario[self.assumptions['lgd_collateral_index']][self.reporting_date:self.maturity_date+relativedelta(months=self.assumptions['lgd_time_to_sale']+1)]
            )
        else:
            return None

    @property
    def effective_interest_rate(self):
        if self.interest_rate_type.upper == 'FLOAT':
            return EffectiveInterestRate.from_assumptions(
                spread=self.spread,
                frequency=self.interest_rate_freq,
                base_rate=self.scenario[self.assumptions['eir_base_rate']][self.reporting_date:self.maturity_date+relativedelta(months=self.assumptions['lgd_time_to_sale']+1)]
            )
        else:
            return EffectiveInterestRate.from_assumptions(spread=self.spread, frequency=self.interest_rate_freq)

    @property
    def exposure_at_default(self):
        return ExposureAtDefault.from_assumptions(
            outstanding_balance=self.outstanding_balance,
            current_arrears=self.current_arrears,
            remaining_term=self.remaining_term,
            contractual_payment=self.contractual_payment,
            contractual_freq=self.contractual_freq,
            effective_interest_rate=self.effective_interest_rate,
            fixed_fees=self.assumptions['ead_fixed_fees'],
            fees_pct=self.assumptions['ead_fees_pct'],
            prepayment_pct=self.assumptions['ead_prepayment_pct']
        )

    @property
    @lru_cache(maxsize=1)
    def transition_matrix(self):
        return TransitionMatrix.from_assumption(
            ttc_transition_matrix=self.assumptions['pd_ttc_transition_matrix'],
            rho=self.assumptions['pd_rho'],
            z=self.scenario[self.assumptions['pd_z']][self.reporting_date:self.maturity_date+relativedelta(months=1)]
        )

    @property
    def probability_of_default(self):
        return ProbabilityOfDefault.from_transition_matrix(
            transition_matrix=self.transition_matrix,
            current_state=self.current_rating
        )

    @property
    def survival(self):
        return Survival.from_assumptions(
            probability_of_default=self.probability_of_default.probability_of_default,
            redemption_rate=self.assumptions['pd_redemption_rate']
        )

    @property
    def loss_given_default(self):
        if self.is_secured:
            return LossGivenDefault.secured_loss_given_default(
                exposure_at_default=self.exposure_at_default[:]*self.outstanding_balance,
                collateral=self.collateral,
                effective_interest_rate=self.effective_interest_rate,
                probability_of_cure=self.assumptions['lgd_probability_of_cure'],
                loss_given_cure=self.assumptions['lgd_loss_given_cure'],
                time_to_sale=self.assumptions['lgd_time_to_sale'],
                forced_sale_discount=self.assumptions['lgd_forced_sale_discount'],
                sales_cost=self.assumptions['lgd_sales_cost'],
                floor=self.assumptions['lgd_floor']
            )
        else:
            return LossGivenDefault.unsecured_loss_given_default(
                probability_of_cure=self.assumptions['lgd_probability_of_cure'],
                loss_given_cure=self.assumptions['lgd_loss_given_cure'],
                loss_given_write_off=self.assumptions['lgd_loss_given_write_off']
            )

    @property
    @lru_cache(maxsize=1)
    def stage_probability(self):
        def add_write_off(X, freq, tts, p_cure):
            """
            Add write-off state to the matrix
            :param X: a single period transition matrix
            :param freq: transition matrix horizon
            :param tts: time to sale / time to write-off
            :param p_cure: probability of cure
            :return: transition matrix with the added write-off state
            """
            rows, columns = X.shape
            temp = np.column_stack((X, zeros(rows)))
            y = zeros(columns + 1)
            y[-1] = 1
            temp = np.vstack((temp, y))

            s = (1 - 1 / tts) ** freq
            c = (1 - s) * p_cure
            wo = (1 - s) * (1 - p_cure)

            z = zeros(columns + 1)
            z[-3:] = c, s, wo
            temp[-2] = z
            return temp

        tm = TransitionMatrix(array([add_write_off(x, 1, self.assumptions['lgd_time_to_sale'], self.assumptions['lgd_probability_of_cure']) for x in self.transition_matrix.transition_matrix]))
        return StageProbability.from_transition_matrix(
            transition_matrix=tm,
            origination_rating=self.origination_rating,
            current_rating=self.current_rating,
            stage_mapping=self.assumptions['stage_map']
        )

    @property
    def model(self):
        return Model(
            stage_probability=self.stage_probability,
            exposure_at_default=self.exposure_at_default,
            survival=self.survival,
            probability_of_default=self.probability_of_default,
            loss_given_default=self.loss_given_default,
            effective_interest_rate=self.effective_interest_rate,
            outstanding_balance=self.outstanding_balance,
            remaining_term=self.remaining_term
        )

    @property
    @lru_cache(maxsize=1)
    def results(self):
        return self.model.results\
            .reset_index()\
            .set_index(
                pd.date_range(
                    start=self.reporting_date,
                    periods=self.remaining_term,
                    freq='M',
                    name='reporting_date'
                )
            )


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
        'XLSX': pd.read_excel,
        'CSV': pd.read_csv
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

    def execute(self, assumptions, scenarios):
        def run_scenario(args):
            name, scenario, assumptions, data = args
            results = []
            for contract_id, d in tqdm(data.iterrows(), desc=f'Model (Scenario: {name})', total=len(data.index)):
                d['assumptions'] = assumptions[d['segment_id']]
                d['scenario'] = scenario
                r = Account(**d).results.assign(**{'contract_id': contract_id, 'scenario': name})
                results.append(r)
            return pd.concat(results)

        args = [(n, s, assumptions, self.data) for n, s in scenarios.items()]
        r = map(run_scenario, args) #thread_map(run_scenario, args, desc='Scenario')
        return pd.concat(r)
