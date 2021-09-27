from scipy.stats import norm as normal
from numpy import array, repeat, stack, insert, append, cumprod, sum
from pandas import Series, DataFrame
from .scenarios import Scenario
from .transition_matrix import TransitionMatrix
from .account import Account
from .assumptions import PDAssumptions

class ConstantProbabilityOfDefault:
    def __init__(self, probability_of_default: float, redemption_rate:float, frequency: int = 12, **kwargs):
        self.probability_of_default = probability_of_default
        self.redemption_rate = redemption_rate
        self.frequency = frequency
        self.hazard = 1 - (1 - self.probability_of_default) ** (1 / self.frequency)
        self.survival = maximum(1 - self.hazard - (1 - (1 - self.redemption_rate) ** (1 / self.frequency)), 0)
    def __getitem__(self, account: Account):
        surival = cumprod(append(1, repeat(self.survival, account.remaining_life-1)))
        return Series(survival * self.hazard, index=account.remaining_life_index)


class MertonVasicekProbabilityOfDefault:
    def __init__(self, probability_of_default: float, rho: float, redemption_rate:float, scenario: Scenario, frequency: int = 12, **kwargs):
        self.probability_of_default = probability_of_default
        self.rho = rho
        self.frequency = frequency
        self.z_index = scenario.z_index
        ttc = normal.ppf(1 - (1 - self.probability_of_default) ** (1 / self.frequency))
        self.hazard = normal.cdf(ttc - self.z_index * (self.rho ** 0.5)/(1 - self.rho) ** 0.5)
        self.surival = maximum(1 - self.hazard - (1 - (1 - self.redemption_rate) ** (1 / self.frequency)), 0)

    def __getitem__(self, account: Account):
        surival = cumprod(append(1, self.survival[account.remaining_life_index][:-1]))
        hazard = self.hazard[account.remaining_life_index]
        return surival * hazard


class TransitionMatrixProbabilityOfDefault:
    def __init__(self, transition_matrix: TransitionMatrix, default_state: int = -1, **kwargs):
        self.transition_matrix = transition_matrix
        self.default_state = default_state

    def __getitem__(self, account: Account):
        s = stack(
            self.transition_matrix.get_cumulative(
                account.remaining_life_index,
                return_list=True
            )
        )[:, account.current_rating, :self.default_state]
        h = stack(self.transition_matrix[account.remaining_life_index])[:, :self.default_state, self.default_state]

        return Series(sum(s * h, axis=1), index=account.remaining_life_index)


class ProbabilityOfDefault:
    @classmethod
    def from_assumptions(cls, assumptions:  PDAssumptions, transition_matrix: TransitionMatrix):
        if assumptions.type.upper() == 'TRANSITION_MATRIX':
            return TransitionMatrixProbabilityOfDefault(transition_matrix, default_state=assumptions.default_state)
        else:
            raise ValueError(f'Only TransitionMatrix PDs are supported.')


