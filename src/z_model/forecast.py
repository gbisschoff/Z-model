from functools import reduce
from operator import __add__
from enum import Enum

from z_model.account import AccountData, SimulatedAccountData
from z_model.assumptions import Assumptions
from z_model.climate_risk_scenarios import ClimateRiskScenarios
from z_model.exeutor import Executor, Methods
from z_model.scenarios import Scenarios


class ForecastType(Enum):
    StaticBalanceSheetForecast = 'static'
    BusinessPlanForecast = 'business_plan'
    DynamicBalanceSheetForecast = 'dynamic'


def static_balance_sheet_forecast(method: Methods, account_data: AccountData, assumptions: Assumptions, scenarios: Scenarios, *args, **kwargs):
    """
    Run the model on actual accounts assuming a closed book.
    """
    return Executor(method=method).execute(
        account_data=account_data,
        assumptions=assumptions,
        scenarios=scenarios,
    )


def business_plan_forecast(method: Methods, account_data: AccountData, assumptions: Assumptions, scenarios: Scenarios, simulated_accounts: SimulatedAccountData, *args, **kwargs):
    """
    Run the model on actual accounts and a set of simulated accounts determined by the business plan.
    """
    return Executor(method=method).execute(
        account_data=account_data + simulated_accounts,
        assumptions=assumptions,
        scenarios=scenarios,
    )


def dynamic_balance_sheet_forecast(method: Methods, account_data: AccountData, assumptions: Assumptions, scenarios: Scenarios, climate_risk_scenarios: ClimateRiskScenarios = None, start=0, stop=60, step=12, *args, **kwargs):
    """
    Run the model multiple times by stepping the reporting date into the future.
    """
    def step_and_execute(args):
        """
        Step the reporting date by one `offset` months and execute the model.
        """
        account_data, assumptions, scenarios, climate_risk_scenarios, offset = args
        return Executor(method=method).execute(
            account_data=account_data.offset(offset),
            assumptions=assumptions,
            scenarios=scenarios,
            climate_risk_scenarios=climate_risk_scenarios
        )

    args = [
        (account_data, assumptions, scenarios, climate_risk_scenarios, m)
        for m in range(start, stop, step)
    ]

    return reduce(__add__, Methods.Map.executor(step_and_execute, args, desc='Steps'))


def forecast(forecast_type: ForecastType, *args, **kwargs):
    """
    Run the forecast method based on forecast_type.
    """
    if forecast_type == ForecastType.BusinessPlanForecast:
        return business_plan_forecast(*args, **kwargs)
    elif forecast_type == ForecastType.StaticBalanceSheetForecast:
        return static_balance_sheet_forecast(*args, **kwargs)
    elif forecast_type == ForecastType.DynamicBalanceSheetForecast:
        return dynamic_balance_sheet_forecast(*args, **kwargs)
    else:
        raise ValueError(f'{forecast_type} is not a valid ForecastType.')
