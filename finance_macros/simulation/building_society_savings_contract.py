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
    starting_capital: float
    savings_rate: float
    savings_interest: float
    mortgage_pay_rate: float
    mortgage_interest: float
    mortgage_downpayment_ratio: float
    contract_sum: float

    savings: InvestmentSimulation
    mortgage: MortgageSimulation

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date,
                 bsc_starting_capital: float, bsc_savings_rate: float, bsc_savings_interest: float,
                 bsc_mortgage_interest: float, bsc_mortgage_pay_rate: Optional[float],
                 bsc_mortgage_downpayment_ratio: float,
                 bsc_contract_sum: float):
        super().__init__(export_directory, identifier, context, start_date, None, (
            lambda _: self.mortgage.d_due_amount[-1] <= 0
        ))
        self.starting_capital = bsc_starting_capital
        self.savings_rate = bsc_savings_rate
        self.savings_interest = bsc_savings_interest
        self.mortgage_pay_rate = bsc_mortgage_pay_rate if (
            bsc_mortgage_pay_rate) else bsc_savings_rate
        self.mortgage_interest = bsc_mortgage_interest
        self.mortgage_downpayment_ratio = bsc_mortgage_downpayment_ratio
        self.contract_sum = bsc_contract_sum

        self.savings = InvestmentSimulation(self.export_directory, self.identifier + "_investment",
                                            self.context,
                                            self.start_date, None,
                                            self.starting_capital,
                                            self.savings_rate, self.savings_interest,
                                            self.contract_sum * self.mortgage_downpayment_ratio)
        self.mortgage = MortgageSimulation(self.export_directory, self.identifier + "_mortgage",
                                           self.context, self.start_date,
                                           None,
                                           self.contract_sum, self.mortgage_downpayment_ratio,
                                           self.mortgage_interest, self.mortgage_pay_rate)

    def simulate(self):
        self.savings.simulate()
        capital = min(self.savings.d_capital[-1], self.contract_sum)
        assert self.savings.end_date
        self.mortgage.start_date = self.savings.end_date
        self.mortgage.downpayment = capital / self.contract_sum
        self.mortgage.reset_data()
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
