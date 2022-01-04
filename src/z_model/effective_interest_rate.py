'''
This module contains the different EIR model implementations.

The EIR model is cofigured via the :class:`EffectiveInterestRate` which acts as an common API to other implementations.

There are two EIR models: :class:`FixedEffectiveInterestRate` and :class:`FloatEffectiveInterestRate`

'''
from numpy import repeat, array
from pandas import Series
from .account import Account
from .scenarios import Scenario
from .assumptions import EIRAssumptions

class FixedEffectiveInterestRate:
    '''
    Fixed Effective Interest Rate

    This class implements the logic to get the account level montly EIR vector from reporting date until the end of
    the contract remaining life.

    The account level interest rate is converted from the interest rate compounding frequency to a monthly EIR used
    by the ECL model, i.e.:

    .. math::
        R_t^(12) = (1 + R_t^(f) / f) ^ (f / 12) - 1

    '''
    def __init__(self, **kwargs):
        pass

    def __getitem__(self, account: Account):
        return Series(repeat((1 + account.fixed_rate/account.interest_rate_freq) ** (account.interest_rate_freq / 12) - 1,  account.remaining_life), index=account.remaining_life_index)

class FloatEffectiveInterestRate:
    '''
    Floating Effective Interest Rate

    This class implements the logic to get the account level montly EIR vector from reporting date until the end of
    the contract remaining life.

    The account level interest rate is converted from the interest rate compounding frequency to a monthly EIR used
    by the ECL model and the base rate is added, i.e.:

    .. math::
        R_t^(12) = (1 + R_t^(f) / f) ^ (f / 12) - 1
        B_t^(1) = (1 + B_t) ^ (1 / 12) - 1
        EIR_t^(12) = R_t^(12) + B_t^(1)

    '''
    def __init__(self, base_rate: array, **kwargs):
        self.base_rate = base_rate

    def __getitem__(self, account: Account):

        return (
            (1 + account.spread / account.interest_rate_freq) ** (account.interest_rate_freq / 12) - 1 +
            (1 + self.base_rate[account.remaining_life_index]) ** (1 / 12) - 1
        )

class EffectiveInterestRate:
    '''
    Effective Interest Rate

    Configure the :class:`FixedEffectiveInterestRate` and :class:`FloatEffectiveInterestRate` models and
    expose a common API to calculate the account specific EIR vector.

    '''
    def __init__(self, fixed_eir: FixedEffectiveInterestRate, float_eir: FloatEffectiveInterestRate):
        self.fixed_eir = fixed_eir
        self.float_eir = float_eir

    def __getitem__(self, account: Account):
        if account.interest_rate_type.upper() == 'FIXED':
            return self.fixed_eir[account]
        elif account.interest_rate_type.upper() == 'FLOAT':
            return self.float_eir[account]
        else:
            return ValueError(f'Invalid interest rate type: {account.contract_id=}, {account.interest_rate_type=}')

    @classmethod
    def from_assumptions(cls, assumptions: EIRAssumptions, scenario: Scenario):
        '''
        Configure the :class:`FixedEffectiveInterestRate` and :class:`FloatEffectiveInterestRate` models.

        :param assumptions: an :class:`EIRAssumptions` object.
        :param scenario: an :class:`Scenario` object.
        '''
        return cls(
            FixedEffectiveInterestRate(),
            FloatEffectiveInterestRate(scenario[assumptions.base_rate])
        )
