from functools import reduce
from operator import __matmul__

from numpy import array, sum, abs, cumsum, newaxis, diff, expand_dims, append, identity, stack, add, tile, flip, \
    subtract, inf, dot, diag, log, exp, fill_diagonal, average, zeros
from numpy.linalg import eig, inv
from pandas import Series, DataFrame
from scipy.stats import norm as normal


def logM(x):
    e_value, e_vector = eig(x)
    Q = e_vector @ diag(log(e_value)) @ inv(e_vector)
    return Q

def expM(Q):
    e_value, e_vector = eig(Q)
    P = e_vector @ diag(exp(e_value)) @ inv(e_vector)
    return P

def powerM(x, t):
    return reduce(__matmul__, [x]*t)

def gmDA(x, t):
    Q = logM(x)/t
    Q[Q<0] = 0
    fill_diagonal(Q, -sum(Q, axis=1))
    diag(Q)
    return Q

def gmWA(x, t):
    n = x.shape[0]
    Q = logM(x)/t
    for i in range(n):
        QiNeg = -sum((Q * (Q<0))[i, [j for j in range(n) if j != i]])
        QiPos = sum((Q * (Q>0))[i, :])
        w = QiNeg/QiPos if (QiNeg != 0) & (QiPos !=0) else 0
        Q[i, [j for j in range(n) if j != i]] = Q[i, [j for j in range(n) if j != i]] - w * Q[i, [j for j in range(n) if j != i]]

    return diag(diag(Q)) + Q*(Q>0)

def gmQO(x,t):
    n = x.shape[0]
    Q = logM(x)/t
    for i in range(n):
        a = Q[i,]
        l = average(a)
        aorder = (a-l).argsort()
        aest = a[aorder]
        for m in range(1, n):
            if ((n - m + 1) * aest[m] - (aest[0] + sum(aest[range(m, n)]))) >= 0:
                mstar = m
                break

        zstar = []
        for j in range(n):
            if j in range(1,mstar):
                zstar.append(0)
            else:
                zstar.append(aest[j] - 1/(n-mstar +1) * (aest[0] + sum(aest[range(mstar, n)])))
        Q[i,] = array(zstar)[aorder.argsort()]
        return Q


def add_write_off(x: array, pcure: float, cure_state: int, time_to_sale: int):
    mu_w = 1 / time_to_sale
    mu_c = (mu_w - (1 - pcure) * mu_w) / (1 - pcure)
    s = exp(-(mu_c + mu_w))
    c = (1 - s) * (pcure)
    w = 1 - s - c

    p = zeros((x.shape[0] + 1, x.shape[1] + 1))
    p[:-1, :-1] = x
    p[-2, -2] = 0
    p[-2, cure_state] = p[-2, cure_state] + c
    p[-2, -2] = p[-2, -2] + s
    p[-2, -1] = p[-2, -1] + w
    p[-1, -1] = 1
    return p


def make_monthly_matrix(x: array, frequency: int, pcure: float, cure_state: int, time_to_sale:int):
    p = expM(gmWA(x, frequency))
    return add_write_off(p, pcure, cure_state, time_to_sale)


class TransitionMatrix:
    def __init__(self, x: Series, default_state: int):
        self.x = x
        self.shape = (len(x), x[0].shape)
        self.default_state = default_state

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

    def get_m_step_probabilities(self, to_state: int, m: int = 12):
        tmv = stack(self)
        stmv = array([reduce(dot, tmv[i:i + m]) for i in range(len(tmv) - m)])
        return DataFrame(stmv[:, :, to_state], index=self.index[:-m])

    @classmethod
    def from_assumption(cls, ttc_transition_matrix: array, rho: float, z: Series, calibrated:bool=False, default_state:int=-1, method:str = 'METHOD-1', **kwargs):

        def standardise(x):
            x[x < 0] = 0
            x = abs(x) / sum(abs(x), axis=1, keepdims=True)
            return x

        ttc = standardise(ttc_transition_matrix)
        zt = z.values[:, newaxis, newaxis]

        if method.upper() == 'METHOD-1':
            cttc = flip(cumsum(flip(ttc, axis=1), axis=1), axis=1)
            cttc[cttc > 1] = 1
            cttc[cttc < 0] = 0

            default_distance = normal.ppf(cttc)
            if calibrated:
                pit = -diff(normal.cdf((default_distance - zt * rho ** 0.5)), append=0)
            else:
                pit = -diff(normal.cdf((default_distance - zt * rho ** 0.5) / (1 - rho) ** 0.5), append=0)

        elif method.upper() == 'METHOD-2':
            cttc = flip(cumsum(flip(ttc, axis=1), axis=1), axis=1)
            cttc[cttc > 1] = 1
            cttc[cttc < 0] = 0

            B = -normal.ppf(cttc)
            DD = tile(B[:, default_state, newaxis], ttc.shape[-1])

            if calibrated:
                pit_dd = ((DD + zt * rho ** 0.5))
            else:
                pit_dd = ((DD + zt * rho ** 0.5) / (1 - rho) ** 0.5)

            BS = tile(subtract(B, DD, out=B, where=abs(B) != inf), (len(z), 1, 1))
            pit = diff(normal.cdf(add(BS, pit_dd, out=BS, where=abs(BS) != inf)), append=1)

        else:
            raise ValueError(f'Method not supported: {method}')

        return cls(Series(list(pit), index=z.index), default_state)
