from datetime import date
from typing import List, Dict

from finance_macros.simulation.core import TimeSeriesSimulation


class InvestmentSimulation(TimeSeriesSimulation):
    starting_capital: float
    monthly_investment: float
    yearly_return: float
    daily_return: float
    _capital: List[float]
    _profit: List[float]

    def __init__(self, start_date: date, end_date: date, starting_capital: float,
                 monthly_investment: float, yearly_return: float,
                 export_directory: str):
        super().__init__(export_directory, start_date, end_date)
        self.starting_capital = starting_capital
        self.monthly_investment = monthly_investment
        self.yearly_return = yearly_return
        self.daily_return = self.calculate_daily_return()
        self._capital = [self.starting_capital]
        self._profit = [0]

    def calculate_daily_return(self) -> float:
        return (1 + self.yearly_return) ** (1 / 365) - 1

    def invest_one_day(self):
        profit = self._capital[-1] * self.daily_return
        self._capital.append(self._capital[-1] + profit)
        self._profit.append(profit)

    def invest_one_month(self):
        self._capital[-1] += self.monthly_investment

    def get_results(self) -> Dict:
        return {"capital": self._capital, "profit": self._profit, "date": self._dates}

    def simulate(self):
        self.call_simulation_functions(
            lambda _: self.invest_one_day(),
            lambda _: self.invest_one_month(),
            1
        )
