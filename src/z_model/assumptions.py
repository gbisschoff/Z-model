from numpy import array
from pandas import read_excel
from pathlib import Path
from .stage_map import StageMap

class PDAssumptions:
    def __init__(self, type: str, z_index: str, rho: float, calibrated: bool, default_state: int, frequency: int, time_in_watchlist: int, transition_matrix: array, method:str):
        self.type = type
        self.z_index = z_index
        self.rho = rho
        self.calibrated = calibrated
        self.default_state = default_state
        self.frequency = frequency
        self.time_in_watchlist = time_in_watchlist
        self.transition_matrix = transition_matrix
        self.method = method


class LGDAssumptions:
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
    def __init__(self, type: str, exposure_at_default:float, ccf_method:str, ccf:str, fees_fixed:float, fees_pct:float, prepayment_pct:float):
        self.type = type
        self.exposure_at_default = exposure_at_default
        self.ccf_method = ccf_method
        self.ccf = ccf
        self.fees_fixed = fees_fixed
        self.fees_pct = fees_pct
        self.prepayment_pct = prepayment_pct


class EIRAssumptions:
    def __init__(self, base_rate:str):
        self.base_rate = base_rate


class SegmentAssumptions:
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
    Container that holds all the assumptions in a nested dictionary.

    Attributes:
        DICTIONARY (dict): Data dictionary of the excel file used to create the assumptions class.
        assumptions (dict): Nested dictionary containing the assumptions.

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
            'pd_default_state': int,
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
        Creates a dictionary of :obj:`Assumptions`.

        Args:
            url: Relative path to the Excel file.
            stage_map: Dictionary containing the staging rules.

        Returns:
            A dictionary of :obj:`Assumptions`.
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
                    default_state = d['pd_default_state'],
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
                    prepayment_pct = d['ead_prepayment_pct']
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
