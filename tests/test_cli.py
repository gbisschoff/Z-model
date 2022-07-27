import pytest
from pathlib import Path
from z_model.__main__ import run, Methods, generate_scenarios, about, ForecastType


def test_about(tmp_path):
    """API Tests"""

    about()


def test_generate_scenarios(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    generate_scenarios(
        assumptions=Path('./data/MONTE_CARLO_ASSUMPTIONS.xlsx'),
        outfile=Path(d / 'out-scenarios.xlsx')
    )
    assert Path(d / 'out-scenarios.xlsx').exists()


def test_static_balancesheet_forecast(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    run(
        forecast_type=ForecastType.StaticBalanceSheetForecast,
        account_data=Path('./data/account-data.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS.xlsx'),
        scenarios=Path('./data/SCENARIOS.xlsx'),
        outfile=Path(d / 'out.zip'),
        method=Methods.ProgressMap
    )
    assert Path(d / 'out.zip').exists()


def test_business_plan_forecast(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    run(
        forecast_type=ForecastType.BusinessPlanForecast,
        account_data=Path('./data/account-data.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS.xlsx'),
        scenarios=Path('./data/SCENARIOS.xlsx'),
        outfile=Path(d / 'out.zip'),
        portfolio_assumptions=Path('./data/PORTFOLIO_ASSUMPTIONS.xlsx'),
        method=Methods.ProgressMap
    )
    assert Path(d / 'out.zip').exists()


def test_dynamic_balancesheet_forecast(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    run(
        forecast_type=ForecastType.DynamicBalanceSheetForecast,
        account_data=Path('./data/account-data.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS.xlsx'),
        scenarios=Path('./data/SCENARIOS.xlsx'),
        outfile=Path(d / 'out.zip'),
        method=Methods.ProgressMap
    )
    assert Path(d / 'out.zip').exists()


def test_climate_risk_forecast(tmp_path):
    """API Tests"""

    d = tmp_path / "data"
    d.mkdir()

    run(
        forecast_type=ForecastType.DynamicBalanceSheetForecast,
        account_data=Path('./data/account-data-cr.xlsx'),
        assumptions=Path('./data/ASSUMPTIONS-cr.xlsx'),
        scenarios=Path('./data/SCENARIOS.xlsx'),
        outfile=Path(d / 'out.zip'),
        climate_risk_scenarios=Path('./data/crva-template.csv'),
        method=Methods.ProgressMap
    )
    assert Path(d / 'out.zip').exists()

