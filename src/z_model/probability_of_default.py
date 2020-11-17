from scipy.stats import norm as normal
from numpy import array, prod as product
from pandas import Series
from .transition_matrix import TransitionMatrix


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
        cumulative_pd_curve = Series(transition_matrix.get_cumulative(0, len(transition_matrix), return_list=True)[1:, current_state, default_state])
        return cls(array(((cumulative_pd_curve - cumulative_pd_curve.shift(1).fillna(0)) / (1 - cumulative_pd_curve.shift(1).fillna(0))).fillna(1)))
