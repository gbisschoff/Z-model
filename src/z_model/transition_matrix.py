from functools import reduce
from operator import __matmul__

from numpy import array, sum, abs, cumsum, newaxis, diff, expand_dims, append, identity, stack, add, tile, flip, \
    subtract, inf, dot, diag, log, exp, fill_diagonal, average, zeros
from numpy.linalg import eig, inv
from pandas import Series, DataFrame
from scipy.stats import norm as normal


def logM(x):
    """Calculate the `log` of a matrix `X` by first performing eigen value decomposition"""
    e_value, e_vector = eig(x)
    Q = e_vector @ diag(log(e_value)) @ inv(e_vector)
    return Q

def expM(Q):
    """Calculate the `exp` of a matrix `X` by first performing eigen value decomposition"""
    e_value, e_vector = eig(Q)
    P = e_vector @ diag(exp(e_value)) @ inv(e_vector)
    return P

def powerM(x, t):
    """Calculate the power of a matrix `X` by multiplying the `X` matrix with it self `t` times"""
    return reduce(__matmul__, [x]*t)

def gmDA(x, t):
    """
    Perform the Diagonal Adjustment (DA) regularisation method on the Generator Matrix
    https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.164.305&rep=rep1&type=pdf
    """
    Q = logM(x)/t
    Q[Q<0] = 0
    fill_diagonal(Q, -sum(Q, axis=1))
    diag(Q)
    return Q

def gmWA(x, t):
    """
    Perform the Weighted Adjustment (WA) regularisation method on the Generator Matrix
    https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.164.305&rep=rep1&type=pdf
    """
    n = x.shape[0]
    Q = logM(x)/t
    for i in range(n):
        QiNeg = -sum((Q * (Q<0))[i, [j for j in range(n) if j != i]])
        QiPos = sum((Q * (Q>0))[i, :])
        w = QiNeg/QiPos if (QiNeg != 0) & (QiPos !=0) else 0
        Q[i, [j for j in range(n) if j != i]] = Q[i, [j for j in range(n) if j != i]] - w * Q[i, [j for j in range(n) if j != i]]

    return diag(diag(Q)) + Q*(Q>0)

def gmQO(x,t):
    """
    Perform the Quasi-optimisation (QO) regularisation method on the Generator Matrix
    https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.164.305&rep=rep1&type=pdf
    """
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
    """Add the  one month probability of cure and probability of write-off to the transition matrix"""
    mu_w = 1 / time_to_sale # Calculate the force of transition to write-off
    mu_c = (mu_w - (1 - pcure) * mu_w) / (1 - pcure) # calculate the force of transition to cure
    s = exp(-(mu_c + mu_w)) # calculate the survival probability (i.e. remain in default)
    c = (1 - s) * (pcure) # calculate the 1m probability of cure
    w = 1 - s - c # calculate the 1m probability of write-off

    p = zeros((x.shape[0] + 1, x.shape[1] + 1)) # Expand the transition matrix to include a write-off state
    p[:-1, :-1] = x # initialise all exisiting probabilities
    p[-2, -2] = 0 # set the 1m survival probability (adjusted later)
    p[-2, cure_state] = p[-2, cure_state] + c # set the 1m cure probability
    p[-2, -2] = p[-2, -2] + s # set the 1m survival probability
    p[-2, -1] = p[-2, -1] + w # set the 1m write-off probability
    p[-1, -1] = 1 # write-off as the absorbing state
    return p


def make_monthly_matrix(x: array, frequency: int, pcure: float, cure_state: int, time_to_sale:int):
    """Transform the transition matrix into a 1m transition matrix using the WA regularisation method, and include the write-off and cure"""
    p = expM(gmWA(x, frequency))
    return add_write_off(p, pcure, cure_state, time_to_sale)


class TransitionMatrix:
    """Transition Matrix

    :param x: a Series of marginal transition matrixes
    :param default_state: the column in the transition matrix associated with Default
    """
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
        """
        Get the cumulative probability matrix as the product of the marginal matrixes

        :param idx: the index of the marginal transition matrixes to use.
        :param return_list: should all cumulative matrixes be returned (True) on only the last cumulative matrix (Default: False).
        """
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
        """
        Calculate the cumulative product of a list of matrixes

        :param l: the list of matrixes to multiply
        :param return_list: should intermediate products be returned (True) or only the last matrix (Default: False)
        """
        if return_list:
            return reduce(lambda a, x: a + [a[-1] @ x] if a else [x], l, [])
        else:
            return reduce(lambda a, x: a @ x if len(a) > 0 else x, l)

    def get_m_step_probabilities(self, to_state: int, m: int = 12):
        """
        Get the probability of transitioning from the stating states to the `to_state` in `m` steps.

        :param to_state: the end state in the matrix
        :param m: the number of steps (Default: 12)
        """
        tmv = stack(self)
        stmv = array([reduce(dot, tmv[i:i + m]) for i in range(len(tmv) - m)])
        return DataFrame(stmv[:, :, to_state], index=self.index[:-m])

    @classmethod
    def from_assumption(cls, ttc_transition_matrix: array, rho: float, z: Series, calibrated:bool=False, default_state:int=-1, method:str = 'METHOD-1', **kwargs):
        """
        Calculate the TransitionMatrix from the model assumptions.

        :param ttc_transition_matrix: the Through-the-Cycle (TTC) probability matrix
        :param rho: the asset correlation, i.e. the correlation between two obligors via a systematic factor Z
        :param z: the systematic factor Z. It should be distributed N(0, 1)
        :param calibrated: (True) should the expected value formula be used (typically used when only a single path of Z
            will be used) or (False) should the raw formula be used (typically used when multiple Z paths will be used)
        :param default_state: the column in the data represeting default
        :param method: The Transition matrix can be made forward in time using two different methods:
            * `METHOD-1` : Use the Z-shift methodology (https://www.z-riskengine.com/media/hqtnwlmb/a-one-parameter-representation-of-credit-risk-and-transition-matrices.pdf)
            * `METHOD-2` : Use the Default Barrier method

        Note that the TTC transition matrix is standardised to ensure there are no negative probabilites.
        """
        def standardise(x):
            x[x < 0] = 0
            x = abs(x) / sum(abs(x), axis=1, keepdims=True)
            return x

        ttc = standardise(ttc_transition_matrix) # standardise the TTC TM to ensure there are no negative probabilities, and rows sum to 100%
        zt = z.values[:, newaxis, newaxis] # Expand Z axix to make numpy broadcasting possible

        if method.upper() == 'METHOD-1':
            cttc = flip(cumsum(flip(ttc, axis=1), axis=1), axis=1) # Calculate the cumulative TTC TM
            cttc[cttc > 1] = 1 # Fix any rounding > 100% to be exactly 100%
            cttc[cttc < 0] = 0 # Fix any rounding < 0% to be exactly 0%

            default_distance = normal.ppf(cttc) # Calculate the TTC default distance
            if calibrated:
                pit = -diff(normal.cdf((default_distance - zt * rho ** 0.5)), append=0) # Calculate the expected PiT PD
            else:
                pit = -diff(normal.cdf((default_distance - zt * rho ** 0.5) / (1 - rho) ** 0.5), append=0) # Calculate the conditional PiT PD

        elif method.upper() == 'METHOD-2':
            cttc = flip(cumsum(flip(ttc, axis=1), axis=1), axis=1) # Calculate the cumulative TTC TM
            cttc[cttc > 1] = 1 # Fix any rounding > 100% to be exactly 100%
            cttc[cttc < 0] = 0 # Fix any rounding < 0% to be exactly 0%

            B = -normal.ppf(cttc) # Calculate the TTC Default Barrier matrix
            DD = tile(B[:, default_state, newaxis], ttc.shape[-1]) # Calculate the TTC Distance to Default matrix

            if calibrated:
                pit_dd = ((DD + zt * rho ** 0.5)) #Calculate the expected PiT DD
            else:
                pit_dd = ((DD + zt * rho ** 0.5) / (1 - rho) ** 0.5) # Calculate the conditional PiT DD

            BS = tile(subtract(B, DD, out=B, where=abs(B) != inf), (len(z), 1, 1)) # Calculate the adjusted Z adjusted default barrier matrix
            pit = diff(normal.cdf(add(BS, pit_dd, out=BS, where=abs(BS) != inf)), append=1) # Calculate the PiT PD (either expected on conditional)

        else:
            raise ValueError(f'Method not supported: {method}')

        return cls(Series(list(pit), index=z.index), default_state)
