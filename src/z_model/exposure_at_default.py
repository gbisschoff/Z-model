from numpy import array
from .effective_interest_rate import EffectiveInterestRate


class ExposureAtDefault:
    def __init__(self, x: array):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, t):
        return self.x[t]

    @property
    def values(self):
        return self.x

    @classmethod
    def from_assumptions(cls, method: str, **kwargs):
        return {
            'CONSTANT': cls.constant,
            'AMORTISING': cls.amortising,
            'CCF': cls.credit_conversion_factor
        }.get(method.upper())(**kwargs)

    @classmethod
    def amortising(cls, outstanding_balance: float, current_arrears: float, remaining_term: int, contractual_payment: float, contractual_freq: int, effective_interest_rate: EffectiveInterestRate, fixed_fees: float = .0, fees_pct: float = .0, prepayment_pct: float = .0, **kwargs):
        balance = [outstanding_balance]
        arrears = [0]
        for t in range(1, remaining_term + 1):
            pmt = contractual_payment if (remaining_term - t) % (12 / contractual_freq) == 0 else 0
            balance.append(max(balance[-1] * (1 + effective_interest_rate[t] + fees_pct - prepayment_pct) + fixed_fees - pmt, 0))
            arrears.append(max(contractual_payment * (1 - (1 + effective_interest_rate[t]) ** min(max(3 - current_arrears / contractual_payment, 1), t * contractual_freq/12)) / (1 - (1 + effective_interest_rate[t])), 0))

        balance = array(balance)
        arrears = array(arrears)
        return cls((balance + arrears)/outstanding_balance)

    @classmethod
    def constant(cls, exposure_at_default: float, remaining_term: int, **kwargs):
        return cls(array([exposure_at_default] * (remaining_term+1)))

    @classmethod
    def credit_conversion_factor(cls, ccf_method: str, outstanding_balance: float, limit: float, ccf: float, remaining_term: int, **kwargs):
        if ccf_method.upper() == 'METHOD 1':
            return cls(array([ccf] * remaining_term))
        elif ccf_method.upper() == 'METHOD 2':
            return cls(array([limit * ccf / outstanding_balance] * remaining_term))
        elif ccf_method.upper() == 'METHOD 3':
            return cls(array([(outstanding_balance + (limit - outstanding_balance) * ccf) / outstanding_balance] * remaining_term))
        else:
            raise ValueError(f'CCF Method ({ccf_method}) not supported.')
