'''
This module contains all the assumptions used by the ECL model. The assumptions are split by:

* :class:`PDAssumptions`: contains the PD model assumption
* :class:`EADAssumptions`: contains the EAD model assumptions
* :class:`LGDAssumptions`: contains the LGD model assumptions
* :class:`EIRAssumptions`: contains the EIR model assumptions
* :class:`SegmentAssumptions`: combined the above assumptions into a class containing all segment assumptions

These are all rolled up into a single :class:`Assumptions` class that contains all the model assumptions for each
segment as a dictionary.

'''
from numpy import array
from pandas import read_excel
from pathlib import Path
from .stage_map import StageMap

class PDAssumptions:
    r'''
    PD Assumptions

    The PD model has the following configurable assumptions:

    :param type: The type of PD model to use. At the moment only ``TRANSITION_MATRIX`` is supported. The transition matrix
        supports both single and multiple default definitions depending on if default is an absorbing state or not.
    :param z_index: The Z-index (Credit Cycle Index) to look up from the :class:`Scenarios` object.
    :param rho: The asset correlation assumption. See the methodology section on how this should be calibrated.
    :param calibrated: True if the model should be calibrated to return the through the cycle PDs if the Z-index is zero.
        If ``False`` the standard Merton Vasicek formula is used:

        .. math::

            PiT = \Phi \left(\frac{TtC - Z\times\sqrt{\rho}}{\sqrt{1-\rho}}\right)

        if ``True`` a the expected value formula is used so that the PiT PD equals the TtC PD if Z is zero,
        i.e.:

        .. math::

            PiT = \Phi(TtC - Z \times \sqrt{\rho})


    :param cure_state: The state on the transition matrix in which accounts cure to. If it is the last column it should be -1,
        if it is the second last column it should be ``-2``.
    :param frequency: The frequency of the transition matrix. By default it should be a 12m transition matrix (``12``).
    :param time_in_watchlist: The number of months an account needs to remain in the watchlist.
        This only has an effect on the stress testing model which does stage forecasting.
    :param transition_matrix The transition matrix used to calculate PDs and stage probabilities. It should be a NxN
        matrix and have an Attrition (A) as the first column in the matrix. If those states should have no effect on the model make the diagonal 100%.
    :param method: What Z-model methodology should be used to calculate the FiT transiton matrixes. Valid values are
        ``METHOD-1`` and ``METHOD-2``. See :class:`TransitionMatrix` for more details.

    '''
    def __init__(self, type: str, z_index: str, rho: float, calibrated: bool, cure_state: int, frequency: int, time_in_watchlist: int, transition_matrix: array, method:str):
        self.type = type
        self.z_index = z_index
        self.rho = rho
        self.calibrated = calibrated
        self.cure_state = cure_state
        self.frequency = frequency
        self.time_in_watchlist = time_in_watchlist
        self.transition_matrix = transition_matrix
        self.method = method


class LGDAssumptions:
    '''
    LGD Assumptions

    The LGD model has the following configurable assumptions:

    :param type: the type of LGD model to use. The following LGD models exist, each with its own set of parameters:

        * ``CONSTANT``: Applies a constant LGD value to all accounts.
        * ``CONSTANT-GROWTH``: Applies a constant growth rate to the collateral value before calculating the LGD.
        * ``INDEXED``: Adjusts the constant LGD by a scaling factor. The scaling factor is calculated as the ratio of
            the index at default date divided by the index at reporting date.
        * ``UNSECURED``: Calculates a constant LGD using the probability of cure, loss given cure and loss given write-
            off.
        * ``SECURED``: Similar to the ``CONSTANT-GROWTH`` LGD, but the collateral value is adjusted by the ratio of the
            index at default date divided by the index at reporting date.

    :param loss_given_default: the ``CONSTANT`` LGD value.
    :param growth_rate: the growth rate applied to the collateral value when using the ``CONSTANT-GROWTH`` LGD model.
    :param index: the index to lookup from the :class:`Scenarios` when using the ``INDEXED`` or ``SECURED`` LGD model.
    :param probability_of_cure: the probability of cure. Used by the ``CONSTANT-GROWTH``, ``UNSECURED`` and ``SECURED``
        LGD model.
    :param loss_given_cure: the loss given cure. Used by the ``CONSTANT-GROWTH``, ``UNSECURED`` and ``SECURED``
        LGD model.
    :param forced_sale_discount: the haircut applied to the collateral value when the collateral is sold. Used by the
        Used by the ``CONSTANT-GROWTH`` and ``SECURED`` LGD model.
    :param sale_cost: the cost of selling the collateral expressed a a percentage of the sale value. Used by the
        Used by the ``CONSTANT-GROWTH`` and ``SECURED`` LGD model.
    :param time_to_sale: The time it takes to sell the collateral. Used by the ``CONSTANT-GROWTH`` and ``SECURED``
        LGD model.
    :param loss_given_write_off: The loss given write-off used by the ``UNSECURED`` LGD model.
    :param floor: The floor applied to the loss given possession. This ensures that the LGD never goes to zero because
        of increases in the collateral value, representing the tail risk. Used by the ``CONSTANT-GROWTH`` and
        ``SECURED`` LGD model.

    '''
    def __init__(self, type:str, loss_given_default:float, growth_rate:float, index:str, probability_of_cure:float, loss_given_cure:float, forced_sale_discount:float, sale_cost:float, time_to_sale:int, loss_given_write_off:float, floor:float):
        self.type = type
        self.loss_given_default = loss_given_default
        self.growth_rate = growth_rate
        self.index = index
        self.probability_of_cure = probability_of_cure
        self.loss_given_cure = loss_given_cure
        self.forced_sale_discount = forced_sale_discount
        self.sale_cost = sale_cost
        self.time_to_sale = time_to_sale
        self.loss_given_write_off = loss_given_write_off
        self.floor = floor


class EADAssumptions:
    '''
    EAD Assumptions

    The EAD model has the following configurable assumptions:

    :param type: the type of EAD model to use. The following models are available:

        * ``CONSTANT``: A constant value is applied to all accounts.
        * ``AMORTISING``: The EAD is calculated using an amortising method. See :class:`ExposureAtDefaul` for more
            information.
        * ``CCF``: The EAD is calculated using a CCF factor. Three different methods are available, see ``ccf_method``
            for more information.

    :param exposure_at_default: the constant EAD to use when the type is ``CONSTANT``.
    :param ccf_method: the CCF method to use. The following method are available:

        * ``METHOD-1``: the ``ccf``  is applied to the outstanding balance

        .. math::
            EAD = outstanding_balance \times ccf

        * ``METHOD-2``: the ``ccf`` is applied to the account limit:

        .. math::
            EAD = limit \times ccf

        * ``METHOD-3``: the ``ccf`` is applied to the unutilised amount;

        .. math::
            EAD = outstanding_balance + (limit - outstanding_balance) \times ccf

    :param ccf: the ccf value used in the above formulas.
    :param fees_fixed: Only used when the ``type`` is ``AMORTISING``. The fixed fees charged each month.
    :param fees_pct: Only used when the ``type`` is ``AMORTISING``. The percentage of the oustanding balance charged
        as fees each month.
    :param prepayment_pct: Only used when the ``type`` is ``AMORTISING``. The percentage overpayment made expressed as
        a percentage of the contractual payment, i.e. 10% implies on average obligors pay
        ``contractual_pmt * (1 + 10%)``

    '''
    def __init__(self, type: str, exposure_at_default:float, ccf_method:str, ccf:str, fees_fixed:float, fees_pct:float, prepayment_pct:float, default_penalty_pct:float, default_penalty_amt:float):
        self.type = type
        self.exposure_at_default = exposure_at_default
        self.ccf_method = ccf_method
        self.ccf = ccf
        self.fees_fixed = fees_fixed
        self.fees_pct = fees_pct
        self.prepayment_pct = prepayment_pct
        self.default_penalty_pct = default_penalty_pct
        self.default_penalty_amt = default_penalty_amt


class EIRAssumptions:
    '''
    EIR Assumptions

    The EIR model has the following configurable assumptions:

    :param base_rate: The base rate index name to look up from the :class:`Scenarios`.
    '''
    def __init__(self, base_rate:str):
        self.base_rate = base_rate


class SegmentAssumptions:
    '''
    Segement Assumptions:

    :class:`SegmentAssumptions` is a container to store all model assumptions associated with a specific segment.


    * :class:`PDAssumptions`: contains the PD model assumption
    * :class:`EADAssumptions`: contains the EAD model assumptions
    * :class:`LGDAssumptions`: contains the LGD model assumptions
    * :class:`EIRAssumptions`: contains the EIR model assumptions

    Each segment is uniquely identified by its ``id`` and a user friendly name is given by ``name``.

    :param id: unique identifier used to lookup the the segment assumptions. Each :class:`Account` is associated with
        a specific segment and thus model configuration.
    :param name: A user friendly name to identify the segment.
    :param pd: An :class:`PDAssumptions` object containing the PD model assumptions.
    :param ead: An :class:`EADAssumptions` object containing the EAD model assumptions.
    :param lgd: An :class:`LGDAssumptions` object containing the LGD model assumptions.
    :param eir: An :class:`EIRAssumptions` object containing the EIR model assumptions.
    :param stage_map: An :class:`StageMap` object containing the IFRS9 staging rules.


    '''
    def __init__(self, id: int, name:str, pd: PDAssumptions, ead:EADAssumptions, lgd:LGDAssumptions, eir:EIRAssumptions, stage_map: StageMap):
        self.id = id
        self.name = name
        self.pd = pd
        self.ead = ead
        self.lgd = lgd
        self.eir = eir
        self.stage_map = stage_map

    def __repr__(self):
        return f'SegmentAssumptions(id={self.id}, name={self.name})'


class Assumptions(dict):
    """
    Container that holds all the segment assumptions in a dictionary ``{id: :class:`SegmentAssumptions`}``.

    """
    DICTIONARY = {
        'ASSUMPTIONS': {
            'segment_name': str,
            'segment_id': int,
            'pd_type': str,
            'pd_method': str,
            'pd_z_index': str,
            'pd_rho': float,
            'pd_calibrated': bool,
            'pd_cure_state': int,
            'pd_frequency': int,
            'pd_time_in_watchlist': int,
            'lgd_type': str,
            'lgd_loss_given_default': float,
            'lgd_growth_rate': float,
            'lgd_index': str,
            'lgd_probability_of_cure': float,
            'lgd_loss_given_cure': float,
            'lgd_forced_sale_discount': float,
            'lgd_sale_cost': float,
            'lgd_time_to_sale': int,
            'lgd_loss_given_write_off': float,
            'lgd_floor': float,
            'ead_type': str,
            'ead_exposure_at_default': float,
            'ead_ccf_method': str,
            'ead_ccf': float,
            'ead_fees_fixed': float,
            'ead_fees_pct': float,
            'ead_prepayment_pct': float,
            'ead_default_penalty_pct': float,
            'ead_default_penalty_amt': float,
            'eir_base_rate': str
        },
        'TRANSITION_MATRIX': {
            'segment_id': int,
            'from': str,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @classmethod
    def from_file(cls, url: Path, *args, **kwargs):
        """
        Creates a dictionary of :obj:`SegementAssumptions` from a Excel file.
        See the descriptions of :class:`PDAssumptions`, :class:`EADAssumptions`, :class:`LGDAssumptions`,
        :class:`EIRAssumptions` and :class:`SegmentAssumptions` for more details on the assumptions.

        The Excel prefixes each assumption with the component name.

        :param url: Relative path to the Excel file.

        """
        assumptions = read_excel(
            io=url,
            sheet_name='ASSUMPTIONS',
            dtype=cls.DICTIONARY['ASSUMPTIONS'],
            index_col='segment_id',
            usecols=cls.DICTIONARY['ASSUMPTIONS'].keys(),
            engine='openpyxl'
        )
        transition_matrices = read_excel(
            io=url,
            sheet_name='TRANSITION_MATRIX',
            dtype=cls.DICTIONARY['TRANSITION_MATRIX'],
            index_col='segment_id',
            engine='openpyxl'
        )
        stage_map = StageMap.from_file(url)

        segments = {
            segment_id: SegmentAssumptions(
                id=segment_id,
                name=d['segment_name'],
                pd=PDAssumptions(
                    type = d['pd_type'],
                    method = d['pd_method'],
                    z_index = d['pd_z_index'],
                    rho = d['pd_rho'],
                    calibrated = d['pd_calibrated'],
                    cure_state = d['pd_cure_state'],
                    frequency = d['pd_frequency'],
                    time_in_watchlist = d['pd_time_in_watchlist'],
                    transition_matrix = array(transition_matrices.drop(columns='from').loc[segment_id]),
                ),
                ead=EADAssumptions(
                    type = d['ead_type'],
                    exposure_at_default = d['ead_exposure_at_default'],
                    ccf_method = d['ead_ccf_method'],
                    ccf = d['ead_ccf'],
                    fees_fixed = d['ead_fees_fixed'],
                    fees_pct = d['ead_fees_pct'],
                    prepayment_pct = d['ead_prepayment_pct'],
                    default_penalty_pct = d['ead_default_penalty_pct'],
                    default_penalty_amt=d['ead_default_penalty_amt']
                ),
                lgd=LGDAssumptions(
                    type = d['lgd_type'],
                    loss_given_default = d['lgd_loss_given_default'],
                    growth_rate = d['lgd_growth_rate'],
                    index = d['lgd_index'],
                    probability_of_cure = d['lgd_probability_of_cure'],
                    loss_given_cure = d['lgd_loss_given_cure'],
                    forced_sale_discount = d['lgd_forced_sale_discount'],
                    sale_cost = d['lgd_sale_cost'],
                    time_to_sale = d['lgd_time_to_sale'],
                    loss_given_write_off = d['lgd_loss_given_write_off'],
                    floor = d['lgd_floor']
                ),
                eir=EIRAssumptions(
                    base_rate=d['eir_base_rate']
                ),
                stage_map=stage_map
            )
            for segment_id, d in assumptions.iterrows()
        }
        return cls(segments)
