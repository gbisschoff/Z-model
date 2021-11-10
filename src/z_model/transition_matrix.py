from scipy.stats import norm as normal
from functools import reduce
from scipy.linalg import fractional_matrix_power
from numpy import array, sum, abs, cumsum, newaxis, diff, expand_dims, append, identity, stack, add, tile, flip, subtract, inf
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
        i = expand_dims(identity(self.shape[-1][0]), axis=0)
        x = append(i, stack(self[idx].values)[:-1], axis=0)

        if return_list:
            return Series(
                self.matrix_cumulative_prod(
                    x,
                    return_list=True
                ),
                index=idx
            )
        else:
            return self.matrix_cumulative_prod(
                x,
                return_list=False
            )


    @staticmethod
    def matrix_cumulative_prod(l, return_list=False):
        if return_list:
            return reduce(lambda a, x: a + [a[-1] @ x] if a else [x], l, [])
        else:
            return reduce(lambda a, x: a @ x if len(a) > 0 else x, l)

    @classmethod
    def from_assumption(cls, ttc_transition_matrix: array, rho: float, z: Series, default_state:int=-1, freq: int = 12, calibrated:bool = True, method:str = 'METHOD-1', **kwargs):

        def fraction_matrix(x, freq):
            rs = fractional_matrix_power(x, 1 / freq)
            rs[rs < 0] = 0
            rs = abs(rs) / sum(abs(rs), axis=1, keepdims=True)
            return rs

        ttc = fraction_matrix(ttc_transition_matrix, freq)
        za = z.values[:, newaxis, newaxis]

        if method.upper() == 'METHOD-1':
            cttc = cumsum(ttc, axis=1)
            cttc[cttc > 1] = 1
            cttc[cttc < 0] = 0

            default_distance = normal.ppf(cttc)

            if calibrated:
                pit = diff(normal.cdf(default_distance + za * (rho ** 0.5) / (1 - rho) ** 0.5), prepend=0)
            else:
                pit = diff(normal.cdf((default_distance + za * rho ** 0.5) / (1 - rho) ** 0.5), prepend=0)

        elif method.upper() == 'METHOD-2':
            cttc = flip(cumsum(flip(ttc, axis=1), axis=1), axis=1)
            cttc[cttc > 1] = 1
            cttc[cttc < 0] = 0

            B = -normal.ppf(cttc)
            DD = tile(B[:, default_state, newaxis], ttc.shape[-1])

            if calibrated:
                pit_dd = (DD - (za * rho ** 0.5) / (1 - rho) ** 0.5)
            else:
                pit_dd = ((DD - za * rho ** 0.5) / (1 - rho) ** 0.5)

            BS = tile(subtract(B, DD, out=B, where=abs(B) != inf), (len(z), 1, 1))
            pit = diff(normal.cdf(add(BS, pit_dd, out=BS, where=abs(BS) != inf)), append=1)

        else:
            raise ValueError(f'Method not supported: {method}')

        return cls(Series(list(pit), index=z.index))
