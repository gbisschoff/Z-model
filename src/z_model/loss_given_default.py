from numpy import array
from .collateral import Collateral
from .effective_interest_rate import EffectiveInterestRate


class LossGivenDefault:
    def __init__(self, loss_given_default: array):
        self.loss_given_default = loss_given_default

    def __len__(self):
        return len(self.loss_given_default)

    def __getitem__(self, t):
        return self.loss_given_default[t]

    @classmethod
    def secured_loss_given_default(cls, probability_of_cure: float, loss_given_cure: float, exposure_at_default: array, collateral: Collateral, time_to_sale: int, forced_sale_discount: float, sales_cost: float, effective_interest_rate: EffectiveInterestRate, floor: float, **kwargs):
        return cls(array([
            probability_of_cure * \
            loss_given_cure + \
            (1 - probability_of_cure) * \
            max(
                (exposure_at_default[t] - collateral[int(t + time_to_sale)] * (1 - forced_sale_discount - sales_cost) /
                 (1 + effective_interest_rate[t: int(t + time_to_sale)])) / exposure_at_default[t],
                floor
            )
            for t in range(len(exposure_at_default))
        ]))

    @classmethod
    def unsecured_loss_given_default(cls, probability_of_cure: float, loss_given_cure: float, loss_given_write_off: float, **kwargs):
        return cls(array([probability_of_cure * loss_given_cure + (1 - probability_of_cure) * loss_given_write_off] * 35 * 12))

    @classmethod
    def constant(cls, loss_given_default: float):
        return cls(array([loss_given_default] * 35 * 12))

    @classmethod
    def from_assumptions(cls, method: str, **kwargs):
        switcher = {
            'SECURED': cls.secured_loss_given_default,
            'UNSECURED': cls.unsecured_loss_given_default,
            'CONSTANT': cls.constant
        }
        return switcher.get(method.upper())(**kwargs)
