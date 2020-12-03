from pandas import DataFrame, pivot_table
from numpy import sum as np_sum


class Results:
    def __init__(self, data: DataFrame):
        self.data = data
        self.long = self._to_long(data)

    @staticmethod
    def _to_long(data):
        rs = data.copy()
        rs = rs.assign(**{
            f'Exposure(t)_{s}': rs['Exposure(t)'] * rs[f'P(S={s})'] / (1 - rs[f'P(S=WO)'])
            for s in [1, 2, 3]
        })
        rs = rs.assign(**{
            f'ECL(t)_{s}': rs[f'Exposure(t)_{s}'] * rs[f'STAGE{s}(t)']
            for s in [1, 2, 3]
        })
        rs.rename(columns={f'P(S={s})': f'P(S=s)_{s}' for s in [1, 2, 3]}, inplace=True)
        rs.drop(columns=['S(t)', 'PD(t)', 'EAD(t)', 'EAD(t+1)', 'LGD(t)', 'LGD(t+1)', 'DF(t+1)', 'Marginal CR(t)',
                         'STAGE1(t)', 'STAGE2(t)', 'STAGE3(t)', 'CR(t)', 'Exposure(t)', 'ECL(t)', 'P(S=WO)'],
                inplace=True)
        rs = rs.melt(
            id_vars=rs.columns.drop(
                sum([[f'P(S=s)_{s}', f'Exposure(t)_{s}', f'ECL(t)_{s}'] for s in [1, 2, 3]], [])
            )
        )
        temp = rs["variable"].str.split("_", n=1, expand=True)
        rs['Stage'] = temp[1]
        rs['variable'] = temp[0]
        rs = rs.pivot(index=rs.columns.drop(['variable', 'value']), columns='variable', values='value').reset_index()
        return rs

    def summarise(self, by=('T', 'scenario', 'Stage')):
        pvt = pivot_table(
            data=self.long,
            index=list(by),
            values=['P(S=s)', 'Exposure(t)', 'ECL(t)'],
            aggfunc=np_sum,
            margins=True,
            margins_name='Total'
        )
        pvt['CR(t)'] = pvt['ECL(t)'] / pvt['Exposure(t)']
        pvt.rename(columns={'P(S=s)': '#'}, inplace=True)
        return pvt[['#', 'Exposure(t)', 'ECL(t)', 'CR(t)']]
