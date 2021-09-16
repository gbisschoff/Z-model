from pandas import DataFrame
from numpy import array, cumprod
from .transition_matrix import TransitionMatrix
from .effective_interest_rate import EffectiveInterestRate
from .loss_given_default import LossGivenDefault
from .stage_probability import StageProbability
from .probability_of_default import ProbabilityOfDefault
from .exposure_at_default import ExposureAtDefault
from .survival import Survival
from .account import Account
from .assumptions import SegmentAssumptions
from .scenarios import Scenario

class ECLModel:
    def __init__(self, stage_probability: StageProbability, exposure_at_default: ExposureAtDefault, survival: Survival, probability_of_default: ProbabilityOfDefault, loss_given_default: LossGivenDefault, effective_interest_rate: EffectiveInterestRate, *args, **kwargs):
        self.stage_probability = stage_probability
        self.exposure_at_default = exposure_at_default
        self.survival = survival
        self.probability_of_default = probability_of_default
        self.loss_given_default = loss_given_default
        self.effective_interest_rate = effective_interest_rate

    def __getitem__(self, account: Account):
        eir = self.effective_interest_rate[account]
        df_t = cumprod(1 + eir) / (1 + eir[0])
        df_t0 = 1 / cumprod(1 + eir)
        s = self.survival[account]
        pd = self.probability_of_default[account]
        ead = self.exposure_at_default[account]
        lgd = self.loss_given_default[account]
        stage_p = self.stage_probability[account]

        marginal_ecl = s * pd * ead * lgd * df_t0
        stage_3_ecl = lgd
        stage_2_ecl_t0 = marginal_ecl[::-1].cumsum()[::-1]
        stage_2_ecl = stage_2_ecl_t0 * df_t
        stage_1_ecl_t0 = stage_2_ecl_t0 - stage_2_ecl_t0.shift(-12).fillna(0)
        stage_1_ecl = stage_1_ecl_t0 * df_t

        coverage_ratio = (
                (
                    stage_p[1] * stage_1_ecl +
                    stage_p[2] * stage_2_ecl +
                    stage_p[3] * stage_3_ecl
                ) /
                (1 - stage_p['wo'])
        )

        exposure = account.outstanding_balance * ead * (1 - stage_p['wo'])
        write_off = account.outstanding_balance * ead * stage_p['wo']
        ecl = exposure * coverage_ratio

        result = DataFrame({
            'contract_id': account.contract_id,
            'T': range(account.remaining_life),
            'forecast_reporting_date': account.remaining_life_index,
            'S(t)': s,
            'PD(t)': pd,
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
        tm = TransitionMatrix.from_assumption(
            ttc_transition_matrix=segment_assumptions.pd.transition_matrix,
            rho=segment_assumptions.pd.rho,
            z=scenario[segment_assumptions.pd.z_index]
        )
        eir = EffectiveInterestRate.from_assumptions(segment_assumptions.eir, scenario)
        sp = StageProbability.from_transition_matrix(
            transition_matrix=tm,
            time_to_sale=segment_assumptions.lgd.time_to_sale,
            probability_of_cure=segment_assumptions.lgd.probability_of_cure,
            stage_map=segment_assumptions.stage_map
        )
        ead = ExposureAtDefault.from_assumptions(segment_assumptions.ead, scenario, eir)
        pd = ProbabilityOfDefault.from_assumptions(segment_assumptions.pd, transition_matrix=tm)
        s = Survival(
            probability_of_default=pd,
            redemption_rate=segment_assumptions.pd.redemption_rate,
            frequency=segment_assumptions.pd.redemption_freq
        )
        lgd = LossGivenDefault.from_assumptions(segment_assumptions.lgd, ead, eir, scenario)

        return cls(sp, ead, s, pd, lgd, eir)
