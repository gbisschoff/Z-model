from numpy import array, maximum, cumprod, insert
from .probability_of_default import ProbabilityOfDefault
from .account import Account

class Survival:
    def __init__(self, probability_of_default: ProbabilityOfDefault, redemption_rate: float, frequency: int = 12):
        self.probability_of_default = probability_of_default
        self.redemption_rate = redemption_rate
        self.frequency = frequency

    def __getitem__(self, account: Account):
        marginal_s = maximum(1 - self.probability_of_default[account] - (1 - (1 - self.redemption_rate) ** (1 / self.frequency)), 0)
        marginal_s = marginal_s.shift(1)
        marginal_s[0] = 1
        return cumprod(marginal_s)

