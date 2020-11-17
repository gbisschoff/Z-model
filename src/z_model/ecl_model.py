from pandas import DataFrame
from numpy import array
from .effective_interest_rate import EffectiveInterestRate
from .loss_given_default import LossGivenDefault
from .stage_probability import StageProbability
from .probability_of_default import ProbabilityOfDefault
from .exposure_at_default import ExposureAtDefault
from .survival import Survival


class ECLModel:
    def __init__(self, stage_probability: StageProbability, exposure_at_default: ExposureAtDefault, survival: Survival, probability_of_default: ProbabilityOfDefault, loss_given_default: LossGivenDefault, effective_interest_rate: EffectiveInterestRate, outstanding_balance: float, remaining_term: int, *args, **kwargs):
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
        result = DataFrame({
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

