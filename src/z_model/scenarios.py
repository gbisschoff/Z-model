from pandas import read_excel, concat, DataFrame, date_range, merge
from numpy import exp
from functools import reduce
from datetime import datetime
from pathlib import Path
from .series import Series
from .file_reader import read_file

class Scenario:
    """
    Container to store a single scenario's data
    """
    def __init__(self, data: DataFrame, method: str = 'linear'):
        data = data.resample('M').interpolate(method)
        data['SCENARIO'] = data['SCENARIO'].interpolate(method='pad')
        self.data = data

    def __getitem__(self, item):
        return self.data[item]


class Scenarios:
    """
    Container to store multiple :class:`Scenario` in a dictionary.
    """
    def __init__(self, x: dict):
        self.x = x

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item]

    def items(self):
        return self.x.items()

    def as_dataframe(self):
        """
        Convert the scenarios to a DataFrame
        """
        return concat([scenario.data for _, scenario in self.items()])

    @property
    def scenarios(self):
        """
        :class:`list`: List of scenario names
        """
        return list(self.x.keys())

    @classmethod
    def from_dataframe(cls, data: DataFrame):
        """
        Create a :class:`Scenarios` object from a data frame.
        """
        return cls({s: Scenario(d) for s, d in data.groupby('SCENARIO')})

    @classmethod
    def from_file(cls, url: Path):
        """
        Create a :class:`Scenarios` object from an Excel file containing scenario data.

        :param url: Relative path to the Excel file.
            The Excel file should be of the following structure::
                {
                    'SCENARIO': str,
                    'DATE': datetime,
                    'VAR_1': float,
                    'VAR_2': float,
                    ...
                }
        """
        data = read_file(
            url=url,
            dtype={
                'SCENARIO': str
            },
            index_col='DATE',
            parse_dates=True
        )
        return cls.from_dataframe(data)

    @classmethod
    def from_assumptions(cls, url: Path):
        """
        Create a `Scenarios` object from an Excel file containing Monte-Carlo assumptions.

        The forecast model is of the form:

        .. math::
            dx = m1 (\theta - x) dt + m2 dx + \sigma dw

        where:

        * ``m1`` is the mean reversion parameter,
        * ``theta`` is the long run average,
        * ``m2`` is the momentum parameter,
        * ``sigma`` is the volatility, and
        * ``dw`` is a Brownian motion.

        :param url: Relative path to the Excel file.
            The Excel file requires the following columns::

            * 'NAME': str - The name of the macroeconomic variable that should be generated. It should match
                (case sensitive) references in other inputs.

            * 'START_DATE': datetime - From when should the macroeconomic forecast start. This should correspond to the
                value of ``x0`` below.

            * 'T': float - The number of periods to forcast. Note that if the model was calibrated on quaterly data,
                this would be the number of quarters to forecast.

            * 'N': int - The length of the output vector. If the model was calibrated on quaterly data and the model
                requires a monthly output vector for the ECL calculations ``N`` would be ``3*T``.

            * 'x0': float - The value of the series at the ``START_DATE``.

            * 'dx0': float - The value of the first difference at the ``START_DATE``, i.e. x(t=0) - x(t=-1).

            * 'theta': float - The Theta parameter in the model. The ``theta`` is the Central Tendency value.

            * 'm1': float - The m1 (mean reversion) parameter in the model.

            * 'm2': float - The m2 (momentum) parameter in the model.

            * 'sigma': float - The models volatility parameter. Set equal to 0 if a deterministic forecast should
                be created.

            * 'm': int - The number of simulations to create.

            * 'fun': str - A transformation to apply to x after the forecast is created. Only ``EXPONENTIAL`` is
                supported at the moment and can be used to convert a variable that was modelled in the Log space to
                the nominal space.

        """
        FUN = {
            'EXPONENTIAL': exp
        }
        assumptions = read_file(
            url=url,
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
            index_col='NAME',
            engine='openpyxl'
        )

        def create_series(name, kwargs):
            start_date = kwargs.pop('START_DATE')
            kwargs['fun'] = FUN.get(kwargs['fun'], lambda x: x)
            forecast = Series(**kwargs)

            forecast_data = DataFrame(forecast.fx.T) \
                .set_index(date_range(start_date, periods=kwargs['N'] + 1, freq='M', name='DATE')) \
                .reset_index() \
                .melt(id_vars='DATE', var_name='SCENARIO', value_name=name)
            forecast_data.SCENARIO = forecast_data.SCENARIO + 1
            return forecast_data

        variables = [create_series(name, args) for name, args in assumptions.iterrows()]
        data = reduce(lambda left, right: merge(left, right, on=['DATE', 'SCENARIO'], how='inner'), variables)\
            .set_index('DATE')
        return cls.from_dataframe(data)
