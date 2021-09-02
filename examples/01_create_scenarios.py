"""
In this example Scenarios are generated using the build in Monte Carlo simulator.

The variables are assumed to follow a mean reverting series with momentum:
    dx = m1*(theta - x)*dt + m2*dx + sigma*dw

Note: By setting sigma = 0 it becomes a deterministic forecast and only a single forecast is required (m=1).

The Excel file (MONTE_CARLO_ASSUMPTIONS.xlsx) contains the parameters to create a set of independent scenarios.
Each row in the excel file creates a new economic variable which is assumed to be independent of the rest.
"""
from pathlib import Path
from z_model.scenarios import Scenarios

scenarios = Scenarios.from_assumptions(url=Path('./data/MONTE_CARLO_ASSUMPTIONS.xlsx'))
scenarios.plot('HPI')

"""
Generated scenarios can be converted to a DataFrame and exported for later use.
"""
scenarios.as_dataframe().to_csv('./data/MONTE_CARLO_SIMULATIONS.csv')

"""
Pre-defined scenarios can also be directly read in from an Excel file using the `.from_file` method.
"""
scenarios = Scenarios.from_file(Path('./data/SCENARIOS.xlsx'))
scenarios.plot('HPI')
