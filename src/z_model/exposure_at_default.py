from numpy import array
from .effective_interest_rate import EffectiveInterestRate


class ExposureAtDefault:
    def __init__(self, exposure_at_default: array):
        self.exposure_at_default = exposure_at_default

    def __len__(self):
        return len(self.exposure_at_default)

    def __getitem__(self, t):
        return self.exposure_at_default[t]

    @classmethod
    def from_assumptions(cls, outstanding_balance: float, current_arrears: float, remaining_term: int, contractual_payment: float, contractual_freq: int, effective_interest_rate: EffectiveInterestRate, fixed_fees: float = .0, fees_pct: float = .0, prepayment_pct: float = .0):
        balance = [outstanding_balance]
        arrears = [0]
        for t in range(1, remaining_term + 1):
            pmt = contractual_payment if (remaining_term - t) % (12 / contractual_freq) == 0 else 0
            balance.append(max(balance[-1] * (1 + effective_interest_rate[t] + fees_pct - prepayment_pct) + fixed_fees - pmt, 0))
            arrears.append(max(contractual_payment * (1 - (1 + effective_interest_rate[t]) ** min(max(3 - current_arrears / contractual_payment, 1), t * contractual_freq/12)) / (1 - (1 + effective_interest_rate[t])), 0))

        balance = array(balance)
        arrears = array(arrears)
        return cls((balance + arrears)/outstanding_balance)
