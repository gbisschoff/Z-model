'''
Probability of Default (PD)

This module contains the different PD models available. The following types are available:

* :class:`ConstantProbabilityOfDefault` - Secured LGD where the collateral value is adjusted by the change in the ``index``.
* :class:`MertonVasicekProbabilityOfDefault` - Unsecured component based LGD.
* :class:`TransitionMatrixProbabilityOfDefault` - Constant LGD value applied to all accounts over time.

:class:`ProbabilityOfDefault` is a common entry point to configure the different PD models and return the segment specfic
PD based on the segment assumptions. Currently on the :class:`TransitionMatrixProbabilityOfDefault` model is supported
in the ECL calculation.

Each PD model exposes a common API to calculate the account specific PD vector.

'''
from scipy.stats import norm as normal
from numpy import array, repeat, stack, insert, append, cumprod, sum
from pandas import Series, DataFrame
from .scenarios import Scenario
from .transition_matrix import TransitionMatrix
from .account import Account
from .assumptions import PDAssumptions

class ConstantProbabilityOfDefault:
    '''
    Constant PD

    The constant PD is calculated as follows. Note that it is the hazard rate that is constant not the PD:

    .. math::
        PD(t) = \prod_(t=0)^t S(t) * Hazard
        S(t) = max( 1 - Hazard - Redemption^(1), 0 )
        Redemption^(1) = 1 - (1 - Redemption^(f))^(1/f)

    '''
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
    '''
    Merton Vasicek PD

    The Merton Vasicek PD is calculated as follows:

    .. math::
        PD(t) = \prod_(t=0)^t S(t) * Hazard(t)
        S(t) = max( 1 - Hazard(t) - Redemption^(1), 0 )
        Redemption^(1) = 1 - (1 - Redemption^(f))^(1/f)
        Hazard(t) = \Phi( (TtCDD - \sqrt(\rho) * Z(t)) / \sqrt(1 - \rho) )
        TtCDD = \phi(TtCPD^(1))
        TtCPD^(1) = 1 - (1 - TtCPD^(f))^(1/f)

    '''
    def __init__(self, probability_of_default: float, rho: float, redemption_rate:float, scenario: Scenario, frequency: int = 12, **kwargs):
        self.probability_of_default = probability_of_default
        self.rho = rho
        self.frequency = frequency
        self.z_index = scenario.z_index
        ttc = normal.ppf(1 - (1 - self.probability_of_default) ** (1 / self.frequency))
        self.hazard = normal.cdf((ttc - self.z_index * (self.rho ** 0.5))/(1 - self.rho) ** 0.5)
        self.surival = maximum(1 - self.hazard - (1 - (1 - self.redemption_rate) ** (1 / self.frequency)), 0)

    def __getitem__(self, account: Account):
        surival = cumprod(append(1, self.survival[account.remaining_life_index][:-1]))
        hazard = self.hazard[account.remaining_life_index]
        return surival * hazard


class TransitionMatrixProbabilityOfDefault:
    '''
    Transition Matrix PD

    The Transition Matrix PD is calculated as follows:

    .. math::
        PD(t) = \sum_{r \not= D} P[R(t)=r | R(t=0) = C] \times P[R(t+1)=D | R(t)=r]

    '''
    def __init__(self, transition_matrix: TransitionMatrix, **kwargs):
        self.transition_matrix = transition_matrix
        self.default_state = transition_matrix.default_state

    def __getitem__(self, account: Account):
        # Calculate the probability of being in each risk grade excl. default (Survival probability)
        s = stack(
            self.transition_matrix.get_cumulative(
                account.remaining_life_index,
                return_list=True
            )
        )[:, account.current_rating, :self.default_state]
        # Calculate the 1m transition to default probability
        h = stack(self.transition_matrix[account.remaining_life_index])[:, :self.default_state, self.default_state]

        # Return the marginal probability of default
        return Series(sum(s * h, axis=1), index=account.remaining_life_index)


class ProbabilityOfDefault:
    @classmethod
    def from_assumptions(cls, assumptions:  PDAssumptions, transition_matrix: TransitionMatrix):
        if assumptions.type.upper() == 'TRANSITION_MATRIX':
            return TransitionMatrixProbabilityOfDefault(transition_matrix)
        else:
            raise ValueError(f'Only TransitionMatrix PDs are supported.')


