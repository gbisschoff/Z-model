from numpy import repeat, array
from pandas import Series
from .account import Account
from .scenarios import Scenario
from .assumptions import EIRAssumptions

class FixedEffectiveInterestRate:
    def __init__(self, **kwargs):
        pass

    def __getitem__(self, account: Account):
        return Series(repeat((1 + account.fixed_rate) ** (1 / account.interest_rate_freq) - 1,  account.remaining_life), index=account.remaining_life_index)

class FloatEffectiveInterestRate:
    def __init__(self, base_rate: array, **kwargs):
        self.base_rate = base_rate

    def __getitem__(self, account: Account):
        return (1 + account.spread + self.base_rate[account.remaining_life_index]) ** (1 /  account.interest_rate_freq) - 1

class EffectiveInterestRate:
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
        return cls(
            FixedEffectiveInterestRate(),
            FloatEffectiveInterestRate(scenario[assumptions.base_rate])
        )
