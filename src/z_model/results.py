from pandas import DataFrame
from numpy import sum


class Results:
    def __init__(self, data: DataFrame):
        self.data = data
        self.long = self._to_long(data)

    @staticmethod
    def _to_long(data):
        rs = data.melt(id_vars=data.columns.drop(['P(S=1)', 'P(S=2)', 'P(S=3)']), var_name='Stage', value_name='P(Stage)')
        rs['Stage'] = rs['Stage'].apply(lambda x: x[-2])
        rs['ECL(t)'] = rs['P(Stage)'] * rs['ECL(t)']
        rs['Exposure(t)'] = rs['P(Stage)'] * rs['Exposure(t)']
        return rs

    def summarise(self, by=('T', 'Stage', 'scenario')):
        rs = self.long.groupby(by=list(by)).agg({'Exposure(t)': sum, 'ECL(t)': sum})
        rs['CR(t)'] = rs['ECL(t)'] / rs['Exposure(t)']
        return rs
