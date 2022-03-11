'''
Loss Given Default (LGD)

This module contains the different LGD models available. The following types are available:

* :class:`SecuredLossGivenDefault` - Secured LGD where the collateral value is adjusted by the change in the ``index``.
* :class:`UnsecuredLossGivenDefault` - Unsecured component based LGD.
* :class:`ConstantLossGivenDefault` - Constant LGD value applied to all accounts over time.
* :class:`ConstantGrowthLossGivenDefault` - Secured LGD where the collateral value is adjusted by a constant growth rate.
* :class:`IndexedLossGivenDefault` - A constant LGD that is adjusted by an scaling factor index.

:class:`LossGivenDefault` is a common entry point to configure the different LGD models and return the segment specfic
LGD model based on the segment assumptions.

Each LGD model exposes a common API to calculate the account specific LGD vector.

'''
from numpy import repeat, array, maximum, zeros, arange
from pandas import Series
from dateutil.relativedelta import relativedelta
from .account import Account
from .scenarios import Scenario
from .effective_interest_rate import EffectiveInterestRate
from .exposure_at_default import ExposureAtDefault
from .assumptions import LGDAssumptions

class SecuredLossGivenDefault:
    '''
    Secured LGD

    The secured LGD is calculated as follows:

    .. math::
        LGD(t) = P[Cure] * LGC + (1 - P[Cure]) * LGP(t)
        LGP(t) = max( (EAD(t) - CollateralValue * CI(t) * (1-FSD) * (1-SC) * df(TTS)) / EAD(t), Floor )
        CI(t) = Index(t + TTS) / Index(t=0)


    '''
    def __init__(self, probability_of_cure: float, loss_given_cure: float, time_to_sale: int, forced_sale_discount: float, sales_cost: float, floor: float, exposure_at_default: ExposureAtDefault, effective_interest_rate: EffectiveInterestRate, index: array, **kwargs):
        self.probability_of_cure = probability_of_cure
        self.loss_given_cure = loss_given_cure
        self.time_to_sale = time_to_sale
        self.forced_sale_discount = forced_sale_discount
        self.sales_cost = sales_cost
        self.floor = floor
        self.exposure_at_default = exposure_at_default
        self.effecive_interest_rate = effective_interest_rate
        self.index = index

    def __getitem__(self, account: Account):
        ead = self.exposure_at_default[account]
        eir = self.effecive_interest_rate[account]
        ci = self.index.shift(-self.time_to_sale)[account.remaining_life_index] / self.index[account.reporting_date]
        df = (1 + eir) ** -self.time_to_sale

        lgd = (
            self.probability_of_cure *
            self.loss_given_cure +
            (1 - self.probability_of_cure) *
            maximum(
                (
                    ead
                    - account.collateral_value * ci * (1 - self.forced_sale_discount) * (1 - self.sales_cost) * df
                ) / ead
                ,self.floor
            )
        )
        return Series(
            lgd,
            index=account.remaining_life_index
        )


class UnsecuredLossGivenDefault:
    '''
    Unsecured LGD

    The unsecured LGD is calculated as follows:

    .. math::
        LGD(t) = P[Cure] * LGC + (1 - P[Cure]) * LGWO

    '''
    def __init__(self, probability_of_cure: float, loss_given_cure: float, loss_given_write_off: float, **kwargs):
        self.probability_of_cure = probability_of_cure
        self.loss_given_cuve = loss_given_cure
        self.loss_given_write_off = loss_given_write_off

    def __getitem__(self, account: Account):
        return Series(
             self.probability_of_cure * self.loss_given_cuve +
             (1 - self.probability_of_cure) * self.loss_given_write_off,
            index=account.remaining_life_index
        )


class ConstantLossGivenDefault:
    '''
    Constant LGD

    The constant LGD is calculated as follows:

    .. math::
        LGD(t) = LGD

    '''
    def __init__(self, loss_given_default: float, **kwargs):
        self.loss_given_default = loss_given_default

    def __getitem__(self, account: Account):
        return Series(
            self.loss_given_default,
            index=account.remaining_life_index
        )

class ConstantGrowthLossGivenDefault:
    '''
    Secured LGD

    The secured LGD is calculated as follows:

    .. math::
        LGD(t) = P[Cure] * LGC + (1 - P[Cure]) * LGP(t)
        LGP(t) = max( (EAD(t) - CollateralValue * CI(t) * (1-FSD) * (1-SC) * df(TTS)) / EAD(t), Floor )
        CI(t) = (1 + GrowthRate)^((t + TTS)/12)

    '''
    def __init__(self, probability_of_cure: float, loss_given_cure: float, time_to_sale: int,
                 forced_sale_discount: float, sales_cost: float, floor: float,
                 exposure_at_default: ExposureAtDefault, effective_interest_rate: EffectiveInterestRate,
                 growth_rate: float, **kwargs):
        self.probability_of_cure = probability_of_cure
        self.loss_given_cure = loss_given_cure
        self.time_to_sale = time_to_sale
        self.forced_sale_discount = forced_sale_discount
        self.sales_cost = sales_cost
        self.floor = floor
        self.exposure_at_default = exposure_at_default
        self.effecive_interest_rate = effective_interest_rate
        self.growth_rate = growth_rate

    def __getitem__(self, account: Account):
        ead = self.exposure_at_default[account]
        eir = self.effecive_interest_rate[account]
        ci = (1 + self.growth_rate) ** ((self.time_to_sale + arange(account.remaining_life)) / 12)
        df = (1 + eir) ** -self.time_to_sale

        lgd = (
            self.probability_of_cure *
            self.loss_given_cure +
            (1 - self.probability_of_cure) *
            maximum(
                (
                    ead
                    - account.collateral_value * ci * (1 - self.forced_sale_discount) * (1 - self.sales_cost) * df
                ) / ead
                ,self.floor
            )
        )
        return Series(
            lgd,
            index=account.remaining_life_index
        )


class IndexedLossGivenDefault:
    '''
    Indexed LGD

    The indexed LGD is calculated as follows:

    .. math::
        LGD(t) = LGD * Index(t) / Index(t=0)

    '''
    def __init__(self, loss_given_default: float, index:array, **kwargs):
        self.loss_given_default = loss_given_default
        self.index = index

    def __getitem__(self, account: Account):
        return Series(
            self.loss_given_default * self.index[account.remaining_life_index] / self.index[account.reporting_date],
            index=account.remaining_life_index
        )

class LossGivenDefault:
    @classmethod
    def from_assumptions(cls, assumptions: LGDAssumptions, ead: ExposureAtDefault, eir: EffectiveInterestRate, scenario: Scenario):
        if assumptions.type.upper() == 'SECURED':
            return SecuredLossGivenDefault(
                probability_of_cure=assumptions.probability_of_cure,
                loss_given_cure=assumptions.loss_given_cure,
                time_to_sale=assumptions.time_to_sale,
                forced_sale_discount=assumptions.forced_sale_discount,
                sales_cost=assumptions.sale_cost,
                floor=assumptions.floor,
                exposure_at_default=ead,
                effective_interest_rate=eir,
                index=scenario[assumptions.index]
            )
        elif assumptions.type.upper() == 'UNSECURED':
            return UnsecuredLossGivenDefault(
                probability_of_cure=assumptions.probability_of_cure,
                loss_given_cure=assumptions.loss_given_cure,
                loss_given_write_off=assumptions.loss_given_write_off
            )
        elif assumptions.type.upper() == 'CONSTANT':
            return ConstantLossGivenDefault(
                loss_given_default=assumptions.loss_given_default
            )
        elif assumptions.type.upper() == 'CONSTANT-GROWTH':
            return ConstantGrowthLossGivenDefault(
                probability_of_cure=assumptions.probability_of_cure,
                loss_given_cure=assumptions.loss_given_cure,
                time_to_sale=assumptions.time_to_sale,
                forced_sale_discount=assumptions.forced_sale_discount,
                sales_cost=assumptions.sale_cost,
                floor=assumptions.floor,
                exposure_at_default=ead,
                effective_interest_rate=eir,
                growth_rate=assumptions.growth_rate
            )
        elif assumptions.type.upper() == 'INDEXED':
            return IndexedLossGivenDefault(
                loss_given_default=assumptions.loss_given_default,
                index=scenario[assumptions.index]
            )
        else:
            raise ValueError(f'Invalid LGD type: {assumptions.type}')