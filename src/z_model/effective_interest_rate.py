from numpy import array, zeros, prod as product


class EffectiveInterestRate:
    def __init__(self, x: array):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return product(1 + self.x[t]) - 1
        else:
            return self.x[t]

    @classmethod
    def from_assumptions(cls, method, **kwargs):
        return {
            'FIXED': cls.fixed_rate,
            'FLOAT': cls.float_rate
        }.get(method.upper())(**kwargs)

    @classmethod
    def fixed_rate(cls, fixed_rate: float, frequency: int = 12, **kwargs):
        return cls(array([(1 + fixed_rate) ** (1 / frequency) - 1] * 35 * 12))

    @classmethod
    def float_rate(cls, spread: float, base_rate: array = None, frequency: int = 12, **kwargs):
        base_rate = zeros(35*12) if base_rate is None else base_rate
        return cls((1 + spread + base_rate) ** (1 / frequency) - 1)
