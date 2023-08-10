"""Mortgage simulation."""
from datetime import date
from typing import List, Optional

from finance_macros.simulation.core import TimeSeriesSimulation, SimulationContext


# pylint: disable=too-many-instance-attributes
class MortgageSimulation(TimeSeriesSimulation):
    """A simulation of a mortgage with a fixed borrowed amount, down payment, interest rate and
    monthly payment. The monthly payment is constant, but the principal and interest paid
    changes according to the remaining due amount (and interest of course)."""
    mortgage_sum: float
    borrowed_amount: float
    downpayment: float
    yearly_interest: float
    monthly_interest: float
    monthly_payment: float
    d_due_amount: List[float]
    d_principal_paid: List[float]
    d_interest_paid: List[float]
    d_paid_cost: List[float]
    d_principal_rate: List[float]
    d_interest_rate: List[float]
    d_net_worth: List[float]
    pay_off_date: Optional[date]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, end_date: Optional[date],
                 mortgage_sum: float,
                 downpayment_ratio: float, interest_rate: float, monthly_payment: float):
        super().__init__(export_directory, identifier, context, start_date, end_date, (
            lambda _: self.d_due_amount[-1] <= 0
        ) if not end_date else None)
        self.mortgage_sum = mortgage_sum
        self.borrowed_amount = mortgage_sum * (1 - downpayment_ratio)
        self.downpayment = mortgage_sum * downpayment_ratio
        self.yearly_interest = interest_rate
        self.monthly_interest = self.calculate_monthly_interest()
        self.monthly_payment = monthly_payment
        self.d_due_amount = [self.borrowed_amount]
        self.d_principal_paid = [0]
        self.d_interest_paid = [0]
        self.d_paid_cost = [self.downpayment]
        self.d_principal_rate = [0]
        self.d_interest_rate = [0]
        self.d_net_worth = [self.mortgage_sum - self.d_due_amount[-1]]

    def calculate_monthly_interest(self) -> float:
        """Calculate the monthly interest rate from the yearly interest rate."""
        return (1 + self.yearly_interest) ** (1 / 12) - 1

    def pay_for_month(self):
        """Simulate a monthly payment."""
        new_interest_paid = self.d_due_amount[-1] * self.monthly_interest
        principal_paid = self.monthly_payment - new_interest_paid
        self.d_interest_paid.append(self.d_interest_paid[-1] + new_interest_paid)
        self.d_principal_paid.append(self.d_principal_paid[-1] + principal_paid)
        self.d_due_amount.append(self.d_due_amount[-1] - principal_paid)
        self.d_paid_cost.append(self.d_paid_cost[-1] + self.monthly_payment)
        self.d_principal_rate.append(principal_paid)
        self.d_interest_rate.append(new_interest_paid)
        self.d_net_worth.append(self.mortgage_sum - self.d_due_amount[-1])

    def get_results(self):
        return {
            "principal_paid": self.d_principal_paid,
            "interest_paid": self.d_interest_paid,
            "due_amount": self.d_due_amount,
            "paid_cost": self.d_paid_cost,
            "principal_rate": self.d_principal_rate,
            "interest_rate": self.d_interest_rate,
            "net_worth": self.d_net_worth,
            "date": self.d_dates
        }

    def simulate(self):
        self.call_simulation_functions(
            monthly_callback=lambda _: self.pay_for_month(),
            day_of_month=1
        )
        try:
            idx = self.d_due_amount.index(next(filter(lambda x: x <= 0, self.d_due_amount)))
            self.pay_off_date = self.d_dates[idx]
        except StopIteration:
            self.pay_off_date = None
        print("Pay off date: ", self.pay_off_date)

    def get_column_names(self) -> List[str]:
        return [
            "principal_paid",
            "interest_paid",
            "due_amount",
            "paid_cost",
            "principal_rate",
            "interest_rate",
            "net_worth",
            "date"
        ]
