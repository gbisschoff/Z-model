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
            'PD(t)': self.probability_of_default.values[0:self.remaining_term],
            'EAD(t)': self.exposure_at_default[0:self.remaining_term],
            'EAD(t+1)': self.exposure_at_default[1:self.remaining_term+1],
            'LGD(t)': self.loss_given_default[0:self.remaining_term],
            'LGD(t+1)': self.loss_given_default[1:self.remaining_term+1],
            'DF(t+1)': array([1 / (1 + self.effective_interest_rate[:t+1]) for t in range(self.remaining_term)]),
            'P(S=1)': self.stage_probability[0:self.remaining_term, 0],
            'P(S=2)': self.stage_probability[0:self.remaining_term, 1],
            'P(S=3)': self.stage_probability[0:self.remaining_term, 2],
            'P(S=WO)': self.stage_probability[0:self.remaining_term, 3],
        }, index=range(self.remaining_term))
        result.index.name = 'T'
        result['Marginal CR(t)'] = result['S(t)'] * result['PD(t)'] * result['EAD(t+1)'] * result['LGD(t+1)'] * result['DF(t+1)']
        result['STAGE1(t)'] = (result['Marginal CR(t)'][::-1].cumsum() - result['Marginal CR(t)'][::-1].cumsum().shift(12).fillna(0)) * result['DF(t+1)'][0] / result['DF(t+1)']
        result['STAGE2(t)'] = result['Marginal CR(t)'][::-1].cumsum() * result['DF(t+1)'][0] / result['DF(t+1)']
        result['STAGE3(t)'] = result['LGD(t)']
        result['CR(t)'] = (result['STAGE1(t)'] * result['P(S=1)'] + result['STAGE2(t)'] * result['P(S=2)'] + result['STAGE3(t)'] * result['P(S=3)']) / (1 - result['P(S=WO)'])
        result['Exposure(t)'] = result['EAD(t)'] * self.outstanding_balance * (1 - result['P(S=WO)'])
        result['Write-off(t)'] = result['EAD(t)'] * self.outstanding_balance * result['P(S=WO)']
        result['ECL(t)'] = result['CR(t)'] * result['Exposure(t)']
        return result
