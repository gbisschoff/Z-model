from numpy import array


class Collateral:
    def __init__(self, value: array):
        self.value = value

    def __len__(self):
        return len(self.value)

    def __getitem__(self, t):
        return self.value[t]

    @classmethod
    def from_assumptions(cls, collateral_value: float, index: array, latest_valuation_date: float = 0):
        return cls(collateral_value * index[latest_valuation_date:]/index[latest_valuation_date])

