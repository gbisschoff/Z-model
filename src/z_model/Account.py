from numpy import array, zeros, column_stack, vstack
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
        def add_write_off(x, freq, tts, p_cure):
            """
            Add write-off state to the matrix
            :param X: a single period transition matrix
            :param freq: transition matrix horizon
            :param tts: time to sale / time to write-off
            :param p_cure: probability of cure
            :return: transition matrix with the added write-off state
            """
            rows, columns = x.shape
            temp = column_stack((x, zeros(rows)))
            y = zeros(columns + 1)
            y[-1] = 1
            temp = vstack((temp, y))

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
                    name='reporting_date'
                )
            )
