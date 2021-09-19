from scipy.stats import norm as normal
from numpy import array, prod as product, repeat, diff, stack, insert, divide, zeros_like
from pandas import Series, DataFrame
from .scenarios import Scenario
from .transition_matrix import TransitionMatrix
from .account import Account
from .assumptions import PDAssumptions

class ConstantProbabilityOfDefault:
    def __init__(self, probability_of_default: float, frequency: int = 12, **kwargs):
        self.probability_of_default = probability_of_default
        self.frequency = frequency
        self.hazard = 1 - (1 - self.probability_of_default) ** (1 / self.frequency)

    def __getitem__(self, account: Account):
        return Series(self.hazard, index=account.remaining_life_index)


class MertonVasicekProbabilityOfDefault:
    def __init__(self, probability_of_default: float, rho: float, scenario: Scenario, frequency: int = 12, **kwargs):
        self.probability_of_default = probability_of_default
        self.rho = rho
        self.frequency = frequency
        self.z_index = scenario.z_index
        ttc = normal.ppf(1 - (1 - self.probability_of_default) ** (1 / self.frequency))
        self.hazard = normal.cdf(ttc - self.z_index * (self.rho ** 0.5)/(1 - self.rho) ** 0.5)

    def __getitem__(self, account: Account):
        return self.hazard[account.remaining_life_index]


class TransitionMatrixProbabilityOfDefault:
    def __init__(self, transition_matrix: TransitionMatrix, default_state: int = -1, **kwargs):
        self.transition_matrix = transition_matrix
        self.default_state = default_state

    def __getitem__(self, account: Account):
        cum = self.transition_matrix.get_cumulative(account.remaining_life_index, return_list=True)
        cum_a = insert(stack(cum)[:, account.current_rating, self.default_state], 0, 0)
        marginal_pd = diff(cum_a)
        s = 1 - cum_a[:-1]
        h = divide(marginal_pd, s, out=zeros_like(s, dtype=float), where=s>0)
        return Series(h, index=account.remaining_life_index)


class ProbabilityOfDefault:
    @classmethod
    def from_assumptions(cls, assumptions:  PDAssumptions, transition_matrix: TransitionMatrix):
        if assumptions.type.upper() == 'TRANSITION_MATRIX':
            return TransitionMatrixProbabilityOfDefault(transition_matrix)
        else:
            raise ValueError(f'Only TransitionMatrix PDs are supported.')


