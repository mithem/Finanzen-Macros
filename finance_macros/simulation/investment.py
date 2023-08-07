"""Investment simulation."""
from datetime import date
from typing import List, Dict

from finance_macros.simulation.core import TimeSeriesSimulation, SimulationContext


class InvestmentSimulation(TimeSeriesSimulation):
    """A simulation of an investment account, with a fixed monthly investment and a fixed yearly
    return."""
    starting_capital: float
    monthly_investment: float
    yearly_return: float
    daily_return: float
    _capital: List[float]
    _profit: List[float]
    _paid_in: List[float]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, end_date: date,
                 starting_capital: float,
                 monthly_investment: float, yearly_return: float):
        super().__init__(export_directory, identifier, context, start_date, end_date)
        self.starting_capital = starting_capital
        self.monthly_investment = monthly_investment
        self.yearly_return = yearly_return
        self.daily_return = self.calculate_daily_return()
        self._capital = [self.starting_capital]
        self._profit = [0]
        self._paid_in = [self.starting_capital]

    def calculate_daily_return(self) -> float:
        """Calculate the daily return from the yearly return."""
        return (1 + self.yearly_return) ** (1 / 365) - 1

    def invest_one_day(self):
        """Simulate one day of investment (not monthly buy-ins)."""
        profit = self._capital[-1] * self.daily_return
        self._capital.append(self._capital[-1] + profit)
        self._profit.append(profit)
        self._paid_in.append(self._paid_in[-1])

    def invest_one_month(self):
        """Simulate the invest-day of the month. Alters the latest simulation parameters to replace
        the day-altered ones."""
        self._capital[-1] += self.monthly_investment
        self._paid_in[-1] += self.monthly_investment

    def get_results(self) -> Dict:
        return {"capital": self._capital, "profit": self._profit, "paid_in": self._paid_in,
                "date": self._dates}

    def simulate(self):
        self.call_simulation_functions(
            lambda _: self.invest_one_day(),
            lambda _: self.invest_one_month(),
            1
        )
