from datetime import date
from typing import List, Optional

from finance_macros.simulation.core import TimeSeriesSimulation, SimulationContext


class MortgageSimulation(TimeSeriesSimulation):
    borrowed_amount: float
    downpayment: float
    yearly_interest: float
    monthly_interest: float
    monthly_payment: float
    _due_amount: List[float]
    _principal_paid: List[float]
    _interest_paid: List[float]
    _paid_cost: List[float]
    _principal_rate: List[float]
    _interest_rate: List[float]
    pay_off_date: Optional[date]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, end_date: date,
                 mortgage_sum: float,
                 downpayment_ratio: float, interest_rate: float, monthly_payment: float):
        super().__init__(export_directory, identifier, context, start_date, end_date)
        self.borrowed_amount = mortgage_sum * (1 - downpayment_ratio)
        self.downpayment = mortgage_sum * downpayment_ratio
        self.yearly_interest = interest_rate
        self.monthly_interest = self.calculate_monthly_interest()
        self.monthly_payment = monthly_payment
        self._due_amount = [self.borrowed_amount]
        self._principal_paid = [0]
        self._interest_paid = [0]
        self._paid_cost = [self.downpayment]
        self._principal_rate = [0]
        self._interest_rate = [0]

    def calculate_monthly_interest(self) -> float:
        return (1 + self.yearly_interest) ** (1 / 12) - 1

    def pay_for_month(self):
        new_interest_paid = self._due_amount[-1] * self.monthly_interest
        principal_paid = self.monthly_payment - new_interest_paid
        self._interest_paid.append(self._interest_paid[-1] + new_interest_paid)
        self._principal_paid.append(self._principal_paid[-1] + principal_paid)
        self._due_amount.append(self._due_amount[-1] - principal_paid)
        self._paid_cost.append(self._paid_cost[-1] + self.monthly_payment)
        self._principal_rate.append(principal_paid)
        self._interest_rate.append(new_interest_paid)

    def get_results(self):
        return {
            "principal_paid": self._principal_paid,
            "interest_paid": self._interest_paid,
            "due_amount": self._due_amount,
            "paid_cost": self._paid_cost,
            "principal_rate": self._principal_rate,
            "interest_rate": self._interest_rate,
            "date": self._dates
        }

    def simulate(self):
        self.call_simulation_functions(
            monthly_callback=lambda _: self.pay_for_month(),
            day_of_month=1
        )
        try:
            idx = self._due_amount.index(next(filter(lambda x: x <= 0, self._due_amount)))
            self.pay_off_date = self._dates[idx]
        except StopIteration:
            self.pay_off_date = None
        print("Pay off date: ", self.pay_off_date)
