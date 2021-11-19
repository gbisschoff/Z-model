from numpy import array, repeat, arange, cumprod, cumsum, maximum, minimum, ceil
from pandas import Series
from .account import Account
from .effective_interest_rate import EffectiveInterestRate
from .assumptions import EADAssumptions
from .scenarios import Scenario

class ConstantExposureAtDefault:
    def __init__(self, exposure_at_default: float):
        self.exposure_at_default = exposure_at_default

    def __getitem__(self, account: Account):
        return Series(self.exposure_at_default, index=account.remaining_life_index)


class AmortisingExposureAtDefault:
    def __init__(self, effective_interest_rate: EffectiveInterestRate, fixed_fees: float = .0, fees_pct: float = .0, prepayment_pct: float = .0, **kwargs):
        self.effective_interest_rate = effective_interest_rate
        self.fixed_fees = fixed_fees
        self.fees_pct = fees_pct
        self.prepayment_pct = prepayment_pct

    def __getitem__(self, account: Account):
        balance = account.outstanding_balance
        t = arange(account.remaining_life) + 1
        eir = self.effective_interest_rate[account]
        df_t0 = 1 / cumprod(1 + eir)

        is_pmt_period = ((account.remaining_life - t) % (12 / account.contractual_freq) == 0)
        n_pmts = cumsum(is_pmt_period)

        pmt = account.contractual_payment * is_pmt_period
        cf = pmt * (1 + self.prepayment_pct) - self.fixed_fees
        cf_t0 = cf * df_t0
        cum_cf_t = cumsum(cf_t0) / df_t0

        balance_t = balance / df_t0 - cum_cf_t
        # Fees are charged before payment is deducted
        fees_pct_amt = cumsum((balance_t + pmt) * self.fees_pct * df_t0)/df_t0
        balance_t_pfees = balance_t + fees_pct_amt

        arrears_allowance = account.contractual_payment * 3
        remaining_allowance = max(arrears_allowance - account.current_arrears, 0)
        remaining_allowance_t = ceil(remaining_allowance / account.contractual_payment)

        arrears_t0 = account.contractual_payment * (n_pmts <= remaining_allowance_t) * is_pmt_period * df_t0
        arrears_t = minimum(cumsum(arrears_t0) / df_t0, remaining_allowance)

        ead = maximum((balance_t_pfees + arrears_t) / account.outstanding_balance, 0)

        return Series(ead, index=account.remaining_life_index)


class CCFExposureAtDefault:
    def __init__(self, ccf_method: str, ccf: float, **kwargs):
        self.ccf_method = ccf_method.upper()
        self.ccf = ccf

    def __getitem__(self, account: Account):
        if self.ccf_method.upper() == 'METHOD 1':
            return Series(
                self.ccf, account.remaining_life,
                index=account.remaining_life_index
            )
        elif self.ccf_method.upper() == 'METHOD 2':
            return Series(
                account.limit * self.ccf / account.outstanding_balance,
                index=account.remaining_life_index
            )
        elif self.ccf_method.upper() == 'METHOD 3':
            return Series(
                (account.outstanding_balance + (account.limit - account.outstanding_balance) * self.ccf) /
                account.outstanding_balance,
                index=account.remaining_life_index
            )
        else:
            raise ValueError(f'CCF Method ({self.ccf_method}) not supported.')


class ExposureAtDefault:
    @classmethod
    def from_assumptions(cls, assumptions: EADAssumptions, scenario: Scenario, eir: EffectiveInterestRate):
        if assumptions.type.upper() =='CONSTANT':
            return ConstantExposureAtDefault(
                exposure_at_default=assumptions.exposure_at_default
            )
        elif assumptions.type.upper() =='AMORTISING':
            return AmortisingExposureAtDefault(
                effective_interest_rate=eir,
                fixed_fees=assumptions.fees_fixed,
                fees_pct=assumptions.fees_pct,
                prepayment_pct=assumptions.prepayment_pct
            )
        elif assumptions.type.upper() =='CCF':
            return CCFExposureAtDefault(
                ccf_method=assumptions.ccf_method,
                ccf=assumptions.ccf
            )
        else:
            raise ValueError(f'Invalid EAD method: {assumptions.type}')
