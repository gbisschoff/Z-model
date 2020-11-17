from numpy import array
from pandas import read_excel


class Assumptions:
    """
    Container that holds all the assumptions in a nested dictionary.
    """
    DICTIONARY = {
        'ASSUMPTIONS': {
            'segment_name': str,
            'segment_id': int,
            'pd_z': str,
            'pd_rho': float,
            'pd_redemption_rate': float,
            'lgd_is_secured': bool,
            'lgd_collateral_index': str,
            'lgd_probability_of_cure': float,
            'lgd_loss_given_cure': float,
            'lgd_forced_sale_discount': float,
            'lgd_sales_cost': float,
            'lgd_time_to_sale': int,
            'lgd_loss_given_write_off': float,
            'lgd_floor': float,
            'ead_fixed_fees': float,
            'ead_fees_pct': float,
            'ead_prepayment_pct': float,
            'eir_base_rate': str
        },
        'TRANSITION_MATRIX': {
            'segment_id': int,
            'from': int,
            'to': int,
            'value': float,
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
    def from_file(cls, url, stage_map):
        assumptions = read_excel(
            io=url,
            sheet_name='ASSUMPTIONS',
            dtype=cls.DICTIONARY['ASSUMPTIONS'],
            index_col='segment_id',
            usecols=cls.DICTIONARY['ASSUMPTIONS'].keys()
        )
        transition_matrices = read_excel(
            io=url,
            sheet_name='TRANSITION_MATRIX',
            dtype=cls.DICTIONARY['TRANSITION_MATRIX'],
            index_col='segment_id',
            usecols=cls.DICTIONARY['TRANSITION_MATRIX'].keys()
        )

        segments = {}
        for segment_id, dct in assumptions.iterrows():
            dct['pd_ttc_transition_matrix'] = array(
                transition_matrices.loc[segment_id].pivot(index='from', columns='to', values='value'))
            dct['stage_map'] = stage_map
            segments[segment_id] = cls(**dct)

        return segments

