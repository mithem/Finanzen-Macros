from datetime import date
from typing import Dict, List

from finance_macros.simulation.core import Simulation, SimulationContext
from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation
from finance_macros.simulation.overlay import Overlay


class RealEstateSimulation(Simulation):
    start_date: date
    buy_price: float
    cash_available: float
    inflation: float
    pay_rate: float
    rent: float
    investment_return: float
    mortgage_interest: float
    target_downpayment: float

    cash_buy_investment: InvestmentSimulation
    immediate_mortgage: MortgageSimulation
    invest_till_downpayment_investment: InvestmentSimulation
    downpayment_mortgage: MortgageSimulation
    overlay: Overlay

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 start_date: date, buy_price: float, cash_available: float, inflation: float,
                 pay_rate: float,
                 rent: float, investment_return: float, mortgage_interest: float,
                 target_downpayment: float):
        super().__init__(export_directory, identifier, context)
        self.start_date = start_date
        self.buy_price = buy_price
        self.cash_available = cash_available
        self.inflation = inflation
        self.pay_rate = pay_rate
        self.rent = rent
        self.investment_return = investment_return
        self.mortgage_interest = mortgage_interest
        self.target_downpayment = target_downpayment

        self.cash_buy_investment = InvestmentSimulation(
            export_directory,
            identifier + "-cash-inv",
            context,
            self.start_date,
            None,
            self.cash_available,
            self.pay_rate,
            self.investment_return,
            self.buy_price
        )
        downpayment_ratio = self.cash_available / self.buy_price
        self.immediate_mortgage = MortgageSimulation(
            export_directory,
            identifier + "-immediate-mortg",
            context,
            self.start_date,
            None,
            self.buy_price,
            downpayment_ratio,
            self.mortgage_interest,
            self.pay_rate + self.rent
        )
        self.invest_till_downpayment_investment = InvestmentSimulation(
            export_directory,
            identifier + "-downpayment-inv",
            context,
            self.start_date,
            None,
            self.cash_available,
            self.pay_rate,
            self.investment_return,
            self.target_downpayment
        )
        self.downpayment_mortgage = MortgageSimulation(
            export_directory,
            identifier + "-downpayment-mortg",
            context,
            self.start_date,
            None,
            self.buy_price,
            self.target_downpayment / self.buy_price,
            self.mortgage_interest,
            self.pay_rate + self.rent
        )
        sims = [self.cash_buy_investment, self.immediate_mortgage,
                self.invest_till_downpayment_investment, self.downpayment_mortgage]
        self.overlay = Overlay(export_directory, identifier, context, sims)

    def simulate(self):
        for sim in [self.cash_buy_investment, self.immediate_mortgage,
                    self.invest_till_downpayment_investment]:
            sim.simulate()
        self.downpayment_mortgage.start_date = self.invest_till_downpayment_investment.end_date
        self.downpayment_mortgage.simulate()

    def get_results(self) -> Dict:
        return self.overlay.get_results()

    def get_column_names(self) -> List[str]:
        return self.overlay.get_column_names()
