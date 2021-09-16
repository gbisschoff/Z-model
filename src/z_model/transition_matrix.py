from scipy.stats import norm as normal
from functools import reduce
from scipy.linalg import fractional_matrix_power
from numpy import array, zeros, identity, append, sum, stack
from pandas import Series, DatetimeIndex
from dateutil.relativedelta import relativedelta

class TransitionMatrix:
    def __init__(self, x: Series):
        self.x = x
        self.shape = (len(x), x[0].shape)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item]

    @property
    def values(self):
        return self.x

    @property
    def index(self):
        return self.x.index

    def get_cumulative(self, idx, return_list=False):
        if return_list:
            return Series(
                self.matrix_cumulative_prod(
                    self[idx],
                    return_list=True
                ),
                index=idx
            )
        else:
            return self.matrix_cumulative_prod(
                self[idx],
                return_list=False
            )


    @staticmethod
    def matrix_cumulative_prod(l, return_list=False):
        if return_list:
            return reduce(lambda a, x: a + [a[-1] @ x] if a else [x], l, [])
        else:
            return reduce(lambda a, x: a @ x if len(a) > 0 else x, l)

    @classmethod
    def from_assumption(cls, ttc_transition_matrix: array, rho: float, z: Series, default_state: int = -1, freq: int = 12, delta: float = 10**-8, **kwargs):

        def fraction_matrix(x, freq):
            temp = fractional_matrix_power(x, 1 / freq)
            temp[temp < 0] = 0
            return standardise(temp)

        def standardise(x, delta=.0):
            return x / (sum(x, axis=1, keepdims=True) * (1+delta))

        def default_distance(ttc_transition_matrix, default_state, delta):
            return -normal.ppf(ttc_transition_matrix[:, default_state] - delta)

        def default_barrier(ttc_transition_matrix, default_state, delta):
            n = len(ttc_transition_matrix)
            default_distance_vector = default_distance(ttc_transition_matrix, default_state, delta)

            default_barrier_matrix = zeros((n, n))
            for i in range(n):
                default_barrier_matrix[:, i] = normal.ppf(sum(ttc_transition_matrix[:, i:], axis=1) - delta) + default_distance_vector

            return default_barrier_matrix

        def z_default_distance(default_distance_vector, rho, z):
            return (default_distance_vector + rho ** 0.5 * z) / (1 - rho) ** 0.5

        def transition_matrix(default_barrier_matrix, z_dd, default_state, delta):
            n = len(default_barrier_matrix)
            matrix = zeros((n, n))

            for i in range(n - 1):
                matrix[:, i] = normal.cdf(default_barrier_matrix[:, i], z_dd) - normal.cdf(default_barrier_matrix[:, i+1], z_dd)
            matrix[:, default_state] = normal.cdf(default_barrier_matrix[:, default_state], z_dd) + delta
            return standardise(matrix)

        ttc_transition_matrix = fraction_matrix(standardise(array(ttc_transition_matrix), delta), freq)
        default_distance_vector = default_distance(ttc_transition_matrix, default_state, delta)
        default_barrier_matrix = default_barrier(ttc_transition_matrix, default_state, delta)
        return cls(
            Series(
                [
                    transition_matrix(default_barrier_matrix, z_default_distance(default_distance_vector, rho, z_i), default_state, delta)
                    for z_i in z
                ],
                index=z.index
            )
        )
