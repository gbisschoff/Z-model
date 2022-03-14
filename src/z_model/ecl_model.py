from pandas import DataFrame
from numpy import array, cumprod
from .transition_matrix import TransitionMatrix, make_monthly_matrix
from .effective_interest_rate import EffectiveInterestRate
from .loss_given_default import LossGivenDefault
from .stage_probability import StageProbability
from .probability_of_default import ProbabilityOfDefault
from .exposure_at_default import ExposureAtDefault
from .account import Account, AccountData
from .assumptions import SegmentAssumptions
from .scenarios import Scenario

class ECLModel:
    r'''
    ECL Model

    This class contains the logic to configure the ECL model as well as calculate the ECL for a given :class:`Account`.

    The discounted marginal ECL at time ``t`` is calculated as:

    .. math::
        ECL(t) = PD(t) \times EAD(t) \times LGD(t) \times df(t)

    From the marginal ECLs the stage conditional ECLs at time ``T`` are calculated as follows:

    .. math::
        ECL(T | S \in {1, 2}) = \sum_{t=T}^{L} ECL(t) / df(T)

        L = \cases {
            min(12, remaining life) & \text{if $S = 1$} \cr
            remaining life & \text{if $S = 2$}
        }

        ECL(T | S=3) = LGD(t)

    Afterwhich, the expected ECL at time T is calculated as the probability weighted average of the stage
    conditional ECLs:

    .. math::
        ECL(T) = \sum_{s \in S} ECL(T | S=s) \times P[S_T = s]

    '''
    def __init__(self, stage_probability: StageProbability, exposure_at_default: ExposureAtDefault, probability_of_default: ProbabilityOfDefault, loss_given_default: LossGivenDefault, effective_interest_rate: EffectiveInterestRate, *args, **kwargs):
        self.stage_probability = stage_probability
        self.exposure_at_default = exposure_at_default
        self.probability_of_default = probability_of_default
        self.loss_given_default = loss_given_default
        self.effective_interest_rate = effective_interest_rate

    def __getitem__(self, account: Account):
        '''
        Calculate the account level ECL forecast.

        :param account: an :class:`Account` object.

        :returns: :class:`DataFrame` with the account level ECL forecast.

        '''
        eir = self.effective_interest_rate[account]
        df_t = cumprod(1 + eir) / (1 + eir[0])
        df_t0 = 1 / cumprod(1 + eir)
        pd = self.probability_of_default[account]
        cpd_12m = pd[::-1].cumsum()[::-1]
        pd_12m = cpd_12m - cpd_12m.shift(-12).fillna(0)
        ead = self.exposure_at_default[account]
        lgd = self.loss_given_default[account]
        stage_p = self.stage_probability[account]

        marginal_ecl = pd * ead * lgd * df_t0
        stage_3_ecl = ead * lgd
        stage_2_ecl_t0 = marginal_ecl[::-1].cumsum()[::-1]
        stage_2_ecl = stage_2_ecl_t0 * df_t
        stage_1_ecl_t0 = stage_2_ecl_t0 - stage_2_ecl_t0.shift(-12).fillna(0)
        stage_1_ecl = stage_1_ecl_t0 * df_t

        exposure = ead * (stage_p[1]+stage_p[2]+stage_p[3])
        ecl = (
            stage_p[1] * stage_1_ecl +
            stage_p[2] * stage_2_ecl +
            stage_p[3] * stage_3_ecl
        )

        coverage_ratio = ecl / exposure
        write_off = ead * stage_p['wo']

        result = DataFrame({
            'contract_id': account.contract_id,
            'T': range(account.remaining_life),
            'forecast_reporting_date': account.remaining_life_index,
            'PD(t)': pd,
            '12mPD(t)': pd_12m,
            'Lifetime PD(t)': cpd_12m,
            'EAD(t)': ead,
            'LGD(t)': lgd,
            'DF(t)': df_t0,
            'P(S=1)': stage_p[1],
            'P(S=2)': stage_p[2],
            'P(S=3)': stage_p[3],
            'P(S=WO)': stage_p['wo'],
            'Marginal CR(t)':marginal_ecl,
            'STAGE1(t)':stage_1_ecl,
            'STAGE2(t)':stage_2_ecl,
            'STAGE3(t)':stage_3_ecl,
            'CR(t)': coverage_ratio,
            'Exposure(t)': exposure,
            'Write-off(t)':write_off,
            'ECL(t)': ecl
        }).set_index('contract_id')

        return result

    @classmethod
    def from_assumptions(cls, segment_assumptions: SegmentAssumptions, scenario: Scenario):
        '''
        Configure the ECL model .

        :param segment_assumptions: object of type :class:`SegmentAssumptions`
        :param scenario: object of type :class:`Scenario`

        '''

        p = make_monthly_matrix(
            x=segment_assumptions.pd.transition_matrix,
            frequency=segment_assumptions.pd.frequency,
            pcure=segment_assumptions.lgd.probability_of_cure,
            cure_state=segment_assumptions.pd.cure_state,
            time_to_sale=segment_assumptions.lgd.time_to_sale
        )

        tm = TransitionMatrix.from_assumption(
            ttc_transition_matrix=p,
            rho=segment_assumptions.pd.rho,
            z=scenario[segment_assumptions.pd.z_index],
            calibrated=segment_assumptions.pd.calibrated,
            default_state=-2, # WO state added when monthly matrix was created
            method=segment_assumptions.pd.method
        )
        eir = EffectiveInterestRate.from_assumptions(segment_assumptions.eir, scenario)
        sp = StageProbability(
            transition_matrix=tm,
            stage_map=segment_assumptions.stage_map,
            time_in_watchlist=segment_assumptions.pd.time_in_watchlist
        )
        ead = ExposureAtDefault.from_assumptions(segment_assumptions.ead, scenario, eir)
        pd = ProbabilityOfDefault.from_assumptions(segment_assumptions.pd, transition_matrix=tm)
        lgd = LossGivenDefault.from_assumptions(segment_assumptions.lgd, ead, eir, scenario)

        return cls(sp, ead, pd, lgd, eir)
