"""
The :class:`ClimateRiskValueAdjustment` class is a container for the value and probability of the climate risk
adjustment. This is then consumed by the LGD model to calculate a climate adjusted LGD and thus ECL.

The :class:`ClimateRiskScenario` class is a factory that is used to produce
:class:`ClimateRiskValueAdjustment`s. It also exposes a method to read the climate risk template (csv) and interpolate
the inputs.

"""
from pathlib import Path
from numpy import array, sum
from pandas import DataFrame, read_csv
from typing import Dict
from warnings import warn

class ClimateRiskValueAdjustment:
    """
    ClimateRiskValueAdjustment

    A container used to store the climate risk value adjustment and the probability.

    :param value: The climate risk value adjustment in LCY.
    :param probability: The probability of the climate risk value adjustment occurring.

    """

    def __init__(self, value: array, probability: array):
        self.value = value
        self.probability = probability

    def _moment_generating_function(self, t):
        """Moment generating function."""
        return ((self.value ** t) * self.probability).sum(axis=1)

    @property
    def expected_value(self):
        """Expected climate risk value adjustment"""
        return self._moment_generating_function(1)

    @property
    def variance(self):
        """The variance of the climate risk value adjustment"""
        return self._moment_generating_function(2) - self.expected_value ** 2

    @property
    def standard_deviation(self):
        """The standard deviation of the climate risk value adjustment"""
        return self.variance ** 0.5


class ClimateRiskScenario:
    """
    ClimateRiskScenario

    A factory class used to produce :class:`ClimateRiskValueAdjustment`s.

    :param data: A :class:`DataFrame` containing the climate risk value adjustments and probabilities, by a UID `key`
        and `date`.
    """
    def __init__(self, data: DataFrame):
        self.data = (
            data
            .reset_index()
            [['key', 'date', 'index', 'value', 'probability']]
            .set_index('key')
        )

    @staticmethod
    def _interpolate(data: DataFrame):
        """
        Interpolate the CRVA between two dates by `key` and `index`.

        :param data: a dataframe containing the `date`, `index`, `value` and `probability`.

        """
        data_expanded = (
            data
            .set_index('date')
            .groupby('index')
            .resample('M')
            .mean()
            .interpolate()
            [['value', 'probability']]
            .reset_index()
        )

        data_expanded['probability'] = (
                data_expanded['probability'] / data_expanded.groupby(['date'])['probability'].transform(sum)
        )

        return data_expanded

    def __getitem__(self, item: tuple) -> ClimateRiskValueAdjustment:
        """
        Get the :class:`ClimateRiskValueAdjustment` for a specific key and date range.

        :param item: A tuple of the form `(key, date_range)` used to look up the specific data.

        """
        key, date_range = item

        try:
            account_data = self.data.loc[key]
            data_expanded = self._interpolate(account_data).pivot(index=['date'], columns=['index'])
            filtered_data = data_expanded.loc[date_range, ['value', 'probability']]

            v = filtered_data['value'].to_numpy()
            p = filtered_data['probability'].to_numpy()

        except KeyError as e:
            # Create empty arrays if an account has no crva - ie assume adjustment is zero
            # warn(f'Account {key} has no CRVA, assuming zero.')
            v = array([[0]])
            p = array([[1]])

        return ClimateRiskValueAdjustment(value=v, probability=p)


class ClimateRiskScenarios:
    def __init__(self, scenarios: Dict[str, ClimateRiskScenario]):
        self.scenarios = scenarios

    def __getitem__(self, scenario: str) -> ClimateRiskScenario:
        return self.scenarios.get(scenario, None)

    def items(self):
        return self.scenarios.items()

    @classmethod
    def from_file(cls, url: Path):
        """Read the climate risk scenario template"""
        data = read_csv(url, parse_dates=['date'], infer_datetime_format=True)
        return ClimateRiskScenarios({s: ClimateRiskScenario(d) for s, d in data.groupby('scenario')})
