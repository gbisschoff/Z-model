from numpy import array, maximum, prod


class Survival:
    def __init__(self, x: array):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, t):
        if isinstance(t, slice):
            return prod(self.x[t])
        else:
            return self.x[t]

    @classmethod
    def from_assumptions(cls, probability_of_default: array, redemption_rate: array):
        return cls(maximum(1 - probability_of_default - redemption_rate, 0))
