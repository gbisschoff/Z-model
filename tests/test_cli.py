import pytest
from pathlib import Path
from z_model.__main__ import run, Methods, generate_scenarios, about


def test_cli(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    about()

    generate_scenarios(
        assumptions=Path('./data/MONTE_CARLO_ASSUMPTIONS.xlsx'),
        outfile=Path(d / 'out-scenarios.csv.gz')
    )
    assert Path(d / 'out-scenarios.csv.gz').exists()

    run(
        account_data=Path('./data/account_level_data.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS.xlsx'),
        scenarios=Path('./data/SCENARIOS.xlsx'),
        outfile=Path(d / 'out.zip'),
        method=Methods.ProgressMap
    )
    assert Path(d / 'out.zip').exists()
