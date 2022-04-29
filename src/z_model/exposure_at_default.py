'''
Exposure at Default (EAD)

This module contains the different EAD models available.

:class:`ExposureAtDefault` is a common entry point to configure the different EAD models and return the segment specfic
EAD model based on the segment assumptions.

Each EAD model exposes a common API to calculate the account specific EAD vector.

The ``Exposure`` of an account is calculated as;

.. math::
    Exposure(t) = OutstandingBalance_(t0) \times EAD(t)

'''
from numpy import array, repeat, arange, cumprod, cumsum, maximum, minimum, ceil
from pandas import Series, isnull
from .account import Account
from .effective_interest_rate import EffectiveInterestRate
from .assumptions import EADAssumptions
from .scenarios import Scenario

class ConstantExposureAtDefault:
    '''
    Constant EAD

    Set the EAD to a constant value over time, i.e.:

    .. math::
       EAD(t) = ExposureAtDefault

    '''
    def __init__(self, exposure_at_default: float):
        self.exposure_at_default = exposure_at_default

    def __getitem__(self, account: Account):
        return Series(account.outstanding_balance * self.exposure_at_default, index=account.remaining_life_index)


class BulletExposureAtDefault:
    '''
    Bullet EAD

    Calculate the EAD using an interest rate calculation method.

    '''
    def __init__(self, effective_interest_rate: EffectiveInterestRate, fixed_fees: float = .0, fees_pct: float = .0, prepayment_pct: float = .0, default_penalty_pct: float = .0, default_penalty_amt: float = .0, **kwargs):
        self.effective_interest_rate = effective_interest_rate
        self.fixed_fees = fixed_fees
        self.fees_pct = fees_pct
        self.prepayment_pct = prepayment_pct
        self.default_penalty_pct = default_penalty_pct
        self.default_penalty_amt = default_penalty_amt

    def __getitem__(self, account: Account):
        balance = account.outstanding_balance
        t = arange(account.remaining_life) + 1
        eir = self.effective_interest_rate[account]
        df_t0 = 1 / cumprod(1 + eir + self.fees_pct - self.prepayment_pct)

        cf = repeat(self.fixed_fees, account.remaining_life)
        cum_cf_t = cumsum(cf * df_t0) / df_t0

        balance_t = maximum(balance / df_t0 + cum_cf_t, 0)
        balance_t_pfees = balance_t * (1 + self.default_penalty_pct) + self.default_penalty_amt

        ead = maximum(balance_t_pfees, 0)

        return Series(ead, index=account.remaining_life_index)


class AmortisingExposureAtDefault:
    '''
    Amortising EAD

    Calculate the EAD using an amortisation table. This is done using the following set of equations:

    .. math::
        EAD(t) = max( (balance(t) + arrears(t)) * (1 + DefaultPenaltyPct) + DefaultPenaltyAmt, 0)
        balance(t) = max( OutstandingBalance / df(t) + ( CumulativeFees(t) - CumulativeCashflows(t) ), 0)
        CumulativeCashflows(t) = \sum_(i=0)^t (ContractualPayment \times I(IsPaymentPeriod(i)) \times (1 + PrepaymentPct) - FixedFees) \times df(i) / df(t)
        CumulativeFees(t) = \sum_(i=0)^t (( balance(i) + ContractualPayment \times I(IsPaymentPeriod(i)) ) \times FeesPct \times df(i)) / df(t)
        arrears(t) = min( CumulativeArrears(t) / df(t), RemainingAllowance)
        CumulativeArrears(t) = \sum_(i=0)^t ContractualPayment * I(NPayments(i) <= RemainingAllowanceT) * I(IsPaymentPeriod(i)) * df(i)
        NPayments(t) = \sum_(i=0)^t I(IsPaymentPeriod(i))
        RemainingAllowanceT = ceil(RemainingAllowance / ContractualPayment)
        RemainingAllowance = max( ContractualPayment * 3 - CurrentArrears, 0)
        I(IsPaymentPeriod(t)) = (RemainingLife - t) % (12 / ContractualFreq) == 0


    '''
    def __init__(self, effective_interest_rate: EffectiveInterestRate, fixed_fees: float = .0, fees_pct: float = .0, prepayment_pct: float = .0, default_penalty_pct: float = .0, default_penalty_amt: float = .0, **kwargs):
        self.effective_interest_rate = effective_interest_rate
        self.fixed_fees = fixed_fees
        self.fees_pct = fees_pct
        self.prepayment_pct = prepayment_pct
        self.default_penalty_pct = default_penalty_pct
        self.default_penalty_amt = default_penalty_amt

    def __getitem__(self, account: Account):
        balance = account.outstanding_balance
        t = arange(account.remaining_life) + 1
        eir = self.effective_interest_rate[account]
        df_t0 = 1 / cumprod(1 + eir)

        is_not_in_payment_holiday = 1 if isnull(account.payment_holiday_end_date) else (account.remaining_life_index >= account.payment_holiday_end_date)
        is_pmt_period = ((account.remaining_life - t) % (12 / account.contractual_freq) == 0) * is_not_in_payment_holiday
        n_pmts = cumsum(is_pmt_period)

        pmt = account.contractual_payment * is_pmt_period
        cf = pmt * (1 + self.prepayment_pct) - self.fixed_fees
        cf_t0 = cf * df_t0
        cum_cf_t = cumsum(cf_t0) / df_t0

        balance_t = balance / df_t0 - cum_cf_t
        # Fees are charged before payment is deducted
        fees_pct_amt = cumsum((balance_t + pmt) * self.fees_pct * df_t0)/df_t0
        balance_t_pfees = maximum(balance_t + fees_pct_amt,0)

        if account.contractual_payment > 0:
            arrears_allowance = account.contractual_payment * 3
            remaining_allowance = max(arrears_allowance - account.current_arrears, 0)
            remaining_allowance_t = ceil(remaining_allowance / account.contractual_payment)

            arrears_t0 = account.contractual_payment * (n_pmts <= remaining_allowance_t) * is_pmt_period * df_t0
            arrears_t = minimum(cumsum(arrears_t0) / df_t0, remaining_allowance)
        else:
            arrears_t = 0

        ead = maximum(((balance_t_pfees + arrears_t) * (1 + self.default_penalty_pct) + self.default_penalty_amt), 0)

        return Series(ead, index=account.remaining_life_index)


class CCFExposureAtDefault:
    '''
    Credit Conversion Factor (CCF) EAD

    Calculate EAD using one of the CCF methods:

    * ``METHOD-1``: EAD(t) = CCF
    * ``METHOD-2``: EAD(t) = AccountLimit * CCF / OutstandingBalancce
    * ``METHOD-3``: EAD(t) = (OutstandingBalance + (AccountLimit - OutstandingBalance) * CCF) / OutstandingBalancce

    '''
    def __init__(self, ccf_method: str, ccf: float, **kwargs):
        self.ccf_method = ccf_method.upper()
        self.ccf = ccf

    def __getitem__(self, account: Account):
        if self.ccf_method.upper() == 'METHOD-1':
            return Series(
                account.outstanding_balance * self.ccf,
                index=account.remaining_life_index
            )
        elif self.ccf_method.upper() == 'METHOD-2':
            return Series(
                account.limit * self.ccf,
                index=account.remaining_life_index
            )
        elif self.ccf_method.upper() == 'METHOD-3':
            return Series(
                (account.outstanding_balance + (account.limit - account.outstanding_balance) * self.ccf),
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
