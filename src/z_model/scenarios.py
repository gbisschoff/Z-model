from pandas import read_excel, concat, Series, DataFrame, date_range, merge
from numpy import exp
from functools import reduce
from datetime import datetime
import seaborn as sns


class Scenario:
    def __init__(self, data: DataFrame):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]


class Scenarios:
    def __init__(self, x: dict):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item]

    def items(self):
        return self.x.items()

    def as_dataframe(self):
        return concat([scenario.data for _, scenario in self.items()])

    def plot(self, item: str):
        data = self.as_dataframe()
        data.SCENARIO = data.SCENARIO.astype(str)
        sns.relplot(data=data, x='DATE', y=item, hue='SCENARIO', kind='line')

    @property
    def scenarios(self):
        return list(self.x.keys())

    @classmethod
    def from_dataframe(cls, data: DataFrame):
        scenarios = dict()
        for s, d in data.groupby('SCENARIO'):
            scenarios[s] = Scenario(d)

        return cls(scenarios)

    @classmethod
    def from_file(cls, url: str):
        data = read_excel(
            io=url,
            sheet_name='DATA',
            dtype={
                'SCENARIO': str,
                'DATE': datetime
            },
            index_col='DATE'
        )
        return cls.from_dataframe(data)

    @classmethod
    def from_assumptions(cls, url: str):
        FUN = {
            'EXPONENTIAL': exp
        }
        assumptions = read_excel(
            io=url,
            sheet_name='DATA',
            dtype={
                'NAME': str,
                'START_DATE': datetime,
                'T': float,
                'N': int,
                'x0': float,
                'dx0': float,
                'theta': float,
                'm1': float,
                'm2': float,
                'sigma': float,
                'm': int,
                'fun': str
            },
            index_col='NAME'
        )

        def create_series(name, args):
            start_date = args.pop('START_DATE')
            args['fun'] = FUN.get(args['fun'], lambda x: x)
            forecast = Series(**args)

            forecast_data = DataFrame(forecast.fx.T) \
                .set_index(date_range(start_date, periods=args['N'] + 1, freq='M', name='DATE')) \
                .reset_index() \
                .melt(id_vars='DATE', var_name='SCENARIO', value_name=name)
            forecast_data.SCENARIO = forecast_data.SCENARIO + 1
            return forecast_data

        variables = [create_series(name, args) for name, args in assumptions.iterrows()]
        data = reduce(lambda left, right: merge(left, right, on=['DATE', 'SCENARIO'], how='inner'), variables)\
            .set_index('DATE')
        return cls.from_dataframe(data)
