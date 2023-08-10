"""Building society savings contract simulation."""
from datetime import date
from typing import Optional, List

from finance_macros.simulation.core import TimeSeriesSimulation, SimulationContext
from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation


# pylint: disable=too-many-instance-attributes
class BuildingSocietySavingsContract(TimeSeriesSimulation):
    """A simulation used to model a building society savings contract (combination of savings
    account and mortgage). You get a guaranteed interest rate on your savings, but are required
    to save a certain amount of money each month. At a later date, the accumulated capital can be
    used to pay off a mortgage at a interest rate defined when signing the contract (before using
    the savings account).
    """
    mortgage_activation_date: date
    starting_capital: float
    savings_rate: float
    savings_interest: float
    mortgage_pay_rate: float
    mortgage_interest: float
    savings_sum: float

    savings: Optional[InvestmentSimulation]
    mortgage: Optional[MortgageSimulation]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, end_date: date,
                 mortgage_activation_date: date,
                 starting_capital: float, savings_rate: float, savings_interest: float,
                 mortgage_interest: float, mortgage_pay_rate: Optional[float],
                 savings_sum: float):
        super().__init__(export_directory, identifier, context, start_date, end_date)
        self.mortgage_activation_date = mortgage_activation_date
        self.starting_capital = starting_capital
        self.savings_rate = savings_rate
        self.savings_interest = savings_interest
        self.mortgage_pay_rate = mortgage_pay_rate if mortgage_pay_rate else savings_rate
        self.mortgage_interest = mortgage_interest
        self.savings_sum = savings_sum

    def simulate(self):
        self.savings = InvestmentSimulation(self.export_directory, self.identifier + "_investment",
                                            self.context,
                                            self.start_date, self.mortgage_activation_date,
                                            self.starting_capital,
                                            self.savings_rate, self.savings_interest)
        self.savings.simulate()
        results = self.savings.get_data()
        capital = min(results["capital"].iloc[-1], self.savings_sum)
        self.mortgage = MortgageSimulation(self.export_directory, self.identifier + "_mortgage",
                                           self.context, self.mortgage_activation_date,
                                           self.end_date,
                                           self.savings_sum, capital / self.savings_sum,
                                           self.mortgage_interest, self.mortgage_pay_rate)
        self.mortgage.simulate()

    def get_results(self):
        assert self.savings
        assert self.mortgage
        savings_results = self.savings.get_results()
        mortgage_results = self.mortgage.get_results()
        results = savings_results.copy()

        # Pad mortgage results in overall results with the first mortgage results' values
        for key in mortgage_results:
            if key != "date":
                results[key] = [0] * len(results["date"])

        # Add mortgage results to overall results
        for key, col in mortgage_results.items():
            results[key] += col

        # Pad savings results in overall results with the last savings results' values
        for key in savings_results:
            if key != "date":
                results[key] += [0] * len(mortgage_results["date"])

        return results

    def get_column_names(self) -> List[str]:
        return ["date", "capital", "interest", "mortgage_interest", "mortgage_pay_rate",
                "mortgage_capital", "mortgage_capital_pay_rate"]
