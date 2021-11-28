import pytest
from pathlib import Path
from z_model.cli import run, Methods


def test_cli(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    run(
        account_data=Path('./data/account_level_data.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS.xlsx'),
        scenarios=Path('./data/MONTE_CARLO_ASSUMPTIONS.xlsx'),
        outfile=Path(d / 'out.csv.gz'),
        detailed_output=Path(d / 'out-detailed.csv.gz'),
        parameter_output=Path(d / 'out-parameters.csv.gz'),
        monte_carlo=Path(d / 'out-scenarios.csv.gz'),
        method=Methods.ProgressMap,
        verbose=True
    )
    assert Path(d / 'out.csv.gz').exists()
    assert Path(d / 'out-detailed.csv.gz').exists()
    assert Path(d / 'out-scenarios.csv.gz').exists()
    assert Path(d / 'out-parameters.csv.gz').exists()
