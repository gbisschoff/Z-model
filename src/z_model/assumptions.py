from numpy import array
from pandas import read_excel
from pathlib import Path
from .stage_map import StageMap

def filter_dict(d: dict, k: str):
    """
    Filter a dictionary for all keys that start with `k`.

    Args:
        d: Dictionary to filter.
        k: String to filter the dictionary with.

    Returns:
        A dictionary with all keys that start with `k`.
    """
    return {key[len(k):]: value for (key, value) in d.items() if key.startswith(k)}


class Assumptions:
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
            'pd_z_index': str,
            'pd_rho': float,
            'pd_redemption_rate': float,
            'lgd_type': str,
            'lgd_loss_given_default': float,
            'lgd_collateral_index': str,
            'lgd_probability_of_cure': float,
            'lgd_loss_given_cure': float,
            'lgd_forced_sale_discount': float,
            'lgd_sales_cost': float,
            'lgd_time_to_sale': int,
            'lgd_loss_given_write_off': float,
            'lgd_floor': float,
            'ead_type': str,
            'ead_exposure_at_default': float,
            'ead_ccf_method': str,
            'ead_ccf': float,
            'ead_fixed_fees': float,
            'ead_fees_pct': float,
            'ead_prepayment_pct': float,
            'eir_base_rate': str
        },
        'TRANSITION_MATRIX': {
            'segment_id': int,
            'from': str,
        }
    }

    def __init__(self, **kwargs):
        self.assumptions = kwargs

    def __getitem__(self, item):
        return self.assumptions[item]

    def __str__(self):
        return str(f'Assumptions({self["segment_name"]})')

    def __repr__(self):
        return str(self)

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
        stage_map = StageMap.from_file(url).x

        segments = {}
        for segment_id, dct in assumptions.iterrows():
            dct['pd_ttc_transition_matrix'] = array(transition_matrices.drop(columns='from').loc[segment_id])
            segments[segment_id] = cls(**{
                'segment_name': dct.get('segment_name', 'Unknown'),
                'segment_id': dct.get('segment_id', 0),
                'stage_map': stage_map,
                'pd': filter_dict(dct, 'pd_'),
                'ead': filter_dict(dct, 'ead_'),
                'lgd': filter_dict(dct, 'lgd_'),
                'eir': filter_dict(dct, 'eir_'),
            })

        return segments
