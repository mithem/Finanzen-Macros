"""Investment simulation."""
from datetime import date
from typing import List, Dict, Optional

from finance_macros.simulation.core import TimeSeriesSimulation, SimulationContext


# pylint: disable=too-many-instance-attributes
class InvestmentSimulation(TimeSeriesSimulation):
    """A simulation of an investment account, with a fixed monthly investment and a fixed yearly
    return."""
    starting_capital: float
    target_capital: Optional[float]
    monthly_investment: float
    yearly_return: float
    daily_return: float
    d_capital: List[float]
    d_profit: List[float]
    d_paid_in: List[float]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, i_end_date: Optional[date],
                 i_starting_capital: float,
                 i_monthly_investment: float, i_yearly_return: float,
                 i_target_capital: Optional[float] = None,
                 automatic_identifier_counting: bool = True):
        assert i_end_date or i_target_capital, "Either end_date or target_capital \
        must be specified."
        self.starting_capital = i_starting_capital
        self.target_capital = i_target_capital
        self.monthly_investment = i_monthly_investment
        self.yearly_return = i_yearly_return
        self.daily_return = self.calculate_daily_return()
        self.d_capital = [self.starting_capital]
        self.d_profit = [0]
        self.d_paid_in = [self.starting_capital]
        super().__init__(export_directory, identifier, context, start_date, i_end_date, (
            lambda _: (
                    self.target_capital is not None and self.d_capital[-1] >= self.target_capital
            )
        ) if self.target_capital else None, automatic_identifier_counting)

    def calculate_daily_return(self) -> float:
        """Calculate the daily return from the yearly return."""
        return (1 + self.yearly_return) ** (1 / 365) - 1

    def invest_one_day(self):
        """Simulate one day of investment (not monthly buy-ins)."""
        profit = self.d_capital[-1] * self.daily_return
        self.d_capital.append(self.d_capital[-1] + profit)
        self.d_profit.append(profit)
        self.d_paid_in.append(self.d_paid_in[-1])

    def invest_one_month(self):
        """Simulate the invest-day of the month. Alters the latest simulation parameters to replace
        the day-altered ones."""
        self.d_capital[-1] += self.monthly_investment
        self.d_paid_in[-1] += self.monthly_investment

    def get_results(self) -> Dict:
        return {"capital": self.d_capital, "profit": self.d_profit, "paid_in": self.d_paid_in,
                "date": self.d_dates}

    def simulate(self):
        self.call_simulation_functions(
            lambda _: self.invest_one_day(),
            lambda _: self.invest_one_month(),
            1
        )

    def get_column_names(self) -> List[str]:
        return ["capital", "profit", "paid_in", "date"]
