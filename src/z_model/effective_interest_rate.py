from numpy import array, zeros, prod as product


class EffectiveInterestRate:
    def __init__(self, effective_interest_rate: array):
        self.effective_interest_rate = effective_interest_rate

    def __len__(self):
        return len(self.effective_interest_rate)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return product(1 + self.effective_interest_rate[t]) - 1
        else:
            return self.effective_interest_rate[t]

    @classmethod
    def from_assumptions(cls, spread: float, base_rate: array = None, frequency: int = 12):
        base_rate = zeros(35*12) if base_rate is None else base_rate
        return cls((1 + spread + base_rate) ** (1 / frequency) - 1)

