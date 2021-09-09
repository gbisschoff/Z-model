from numpy import array, zeros
from pandas import date_range
from dateutil.relativedelta import relativedelta
from functools import lru_cache
from .assumptions import Assumptions
from .scenarios import Scenario
from .collateral import Collateral
from .transition_matrix import TransitionMatrix
from .effective_interest_rate import EffectiveInterestRate
from .loss_given_default import LossGivenDefault
from .stage_probability import StageProbability
from .probability_of_default import ProbabilityOfDefault
from .exposure_at_default import ExposureAtDefault
from .ecl_model import ECLModel
from .survival import Survival


class Account:
    def __init__(self, assumptions: Assumptions, scenario: Scenario, outstanding_balance, current_arrears, contractual_payment, contractual_freq, interest_rate_type, interest_rate_freq, fixed_rate, spread, origination_date, maturity_date, reporting_date, collateral_value, origination_rating, current_rating, watchlist, *args, **kwargs):
        self.assumptions = assumptions
        self.scenario = scenario
        self.outstanding_balance = outstanding_balance
        self.current_arrears = current_arrears
        self.interest_rate_type = interest_rate_type
        self.interest_rate_freq = interest_rate_freq
        self.fixed_rate = fixed_rate
        self.spread = spread
        self.origination_date = origination_date
        self._maturity_date = maturity_date
        self.reporting_date = reporting_date
        self.collateral_value = collateral_value
        self.contractual_payment = contractual_payment
        self.contractual_freq = contractual_freq
        self.origination_rating = origination_rating
        self.current_rating = current_rating
        self.watchlist = watchlist

    @property
    def maturity_date(self):
        return max(self._maturity_date, self.reporting_date + relativedelta(months=1))

    @property
    def remaining_term(self):
        return max(self.term - self.time_on_book, 1)

    @property
    def past_maturity(self):
        return self._maturity_date <= self.reporting_date

    @property
    def time_on_book(self):
        return (self.reporting_date.year - self.origination_date.year) * 12 + \
               (self.reporting_date.month - self.origination_date.month)

    @property
    def term(self):
        return (self.maturity_date.year - self.origination_date.year) * 12 + \
               (self.maturity_date.month - self.origination_date.month)

    @property
    def collateral_index(self):
        return self.scenario[self.assumptions['lgd']['collateral_index']][self.reporting_date:self.maturity_date+relativedelta(months=self.assumptions['lgd']['time_to_sale']+1)]

    @property
    def z_index(self):
        return self.scenario[self.assumptions['pd']['z_index']][self.reporting_date:self.maturity_date+relativedelta(months=1)]

    @property
    def base_rate(self):
        return self.scenario[self.assumptions['eir']['base_rate']][
            self.reporting_date:self.maturity_date + relativedelta(months=self.assumptions['lgd']['time_to_sale'] + 1)]

    @property
    def collateral(self):
        if self.assumptions['lgd']['type'].upper() == 'SECURED':
            return Collateral.from_assumptions(
                collateral_value=self.collateral_value,
                index=self.collateral_index
            )
        else:
            return None

    @property
    def effective_interest_rate(self):
        return EffectiveInterestRate.from_assumptions(
            method=self.interest_rate_type,
            fixed_rate=self.fixed_rate,
            spread=self.spread,
            frequency=self.interest_rate_freq,
            base_rate=self.base_rate
        )

    @property
    def exposure_at_default(self):
        return ExposureAtDefault.from_assumptions(
            method=self.assumptions['ead']['type'],
            outstanding_balance=self.outstanding_balance,
            current_arrears=self.current_arrears,
            remaining_term=self.remaining_term,
            contractual_payment=self.contractual_payment,
            contractual_freq=self.contractual_freq,
            effective_interest_rate=self.effective_interest_rate,
            **self.assumptions['ead']
        )

    @property
    @lru_cache(maxsize=1)
    def transition_matrix(self):
        return TransitionMatrix.from_assumption(
            ttc_transition_matrix=self.assumptions['pd']['ttc_transition_matrix'],
            rho=self.assumptions['pd']['rho'],
            z=self.z_index
        )

    @property
    @lru_cache(maxsize=1)
    def probability_of_default(self):
        return ProbabilityOfDefault.from_assumptions(
            method=self.assumptions['pd']['type'],
            transition_matrix=self.transition_matrix,
            current_state=self.current_rating,
            z=self.z_index,
            rho=self.assumptions['pd']['rho']
        )

    @property
    def survival(self):
        return Survival.from_assumptions(
            probability_of_default=self.probability_of_default.values,
            redemption_rate=self.assumptions['pd']['redemption_rate']
        )

    @property
    def loss_given_default(self):
        return LossGivenDefault.from_assumptions(
            method=self.assumptions['lgd']['type'],
            exposure_at_default=self.exposure_at_default.values * self.outstanding_balance,
            collateral=self.collateral,
            effective_interest_rate=self.effective_interest_rate,
            **self.assumptions['lgd']
        )

    @property
    @lru_cache(maxsize=1)
    def stage_probability(self):
        def add_write_off(x, freq, tts, p_cure):
            """
            Add write-off state to the matrix
            :param x: a single period transition matrix
            :param freq: transition matrix horizon
            :param tts: time to sale / time to write-off
            :param p_cure: probability of cure
            :return: transition matrix with the added write-off state
            """
            rows, columns = x.shape

            s = (1 - 1 / tts) ** freq
            c = (1 - s) * p_cure
            wo = (1 - s) * (1 - p_cure)

            x_new = zeros((rows + 1, columns + 1), dtype=x.dtype)
            x_new[0:rows, 0:columns] = x
            x_new[-1, -1] = 1
            x_new[-2, -3:] = c, s, wo

            return x_new

        tm = array([add_write_off(x, 1, self.assumptions['lgd']['time_to_sale'], self.assumptions['lgd']['probability_of_cure']) for x in self.transition_matrix.values])
        return StageProbability.from_transition_matrix(
            transition_matrix=TransitionMatrix(tm),
            origination_rating=self.origination_rating,
            current_rating=self.current_rating,
            stage_mapping=self.assumptions['stage_map'],
            watchlist=self.watchlist
        )

    @property
    def model(self):
        return ECLModel(
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
                date_range(
                    start=self.reporting_date,
                    periods=self.remaining_term,
                    freq='M',
                    name='forecast_reporting_date'
                )
            )
