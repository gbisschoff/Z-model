from scipy.stats import norm as normal
from numpy import array, prod as product
from pandas import Series
from .transition_matrix import TransitionMatrix


class ProbabilityOfDefault:
    def __init__(self, x: array):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return 1 - product(1 - self.x[t])
        else:
            return self.x[t]

    @property
    def values(self):
        return self.x

    @classmethod
    def from_assumptions(cls, method: str, **kwargs):
        return {
            'CONSTANT': cls.constant,
            'MERTON_VASICEK': cls.merton_vasicek,
            'TRANSITION_MATRIX': cls.transition_matrix
        }.get(method.upper())(**kwargs)

    @classmethod
    def transition_matrix(cls, transition_matrix: TransitionMatrix, current_state: int, default_state: int = -1, **kwargs):
        cumulative_pd_curve = Series(transition_matrix.get_cumulative(0, len(transition_matrix), return_list=True)[1:, current_state, default_state])
        return cls(array(((cumulative_pd_curve - cumulative_pd_curve.shift(1).fillna(0)) / (1 - cumulative_pd_curve.shift(1).fillna(0))).fillna(1)))

    @classmethod
    def merton_vasicek(cls, ttc_probability_of_default: float, rho: float, z: array, freq: int = 12, **kwargs):
        return cls(normal.cdf((normal.ppf(1 - (1-ttc_probability_of_default) ** (1/freq)) - rho ** 0.5 * z) / (1-rho) ** 0.5))

    @classmethod
    def constant(cls, ttc_probability_of_default: float, freq: int = 12, **kwargs):
        return cls(array([1 - (1-ttc_probability_of_default) ** (1/freq)] * 35 * 12))
