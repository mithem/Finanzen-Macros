import re
from datetime import date
from typing import Optional, Type, List, Callable

from finance_macros.simulation.building_society_savings_contract import \
    BuildingSocietySavingsContract
from finance_macros.simulation.core import T, UserError, Overlay, SimulationContext
from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation


class CLIArgument:
    key: str
    display_name: Optional[str]
    type: Type
    optional: bool
    default: T
    choices_provider: Optional[Callable]

    def __init__(self, key: str, type_: Type, optional: bool = False, default: T = None,
                 display_name: Optional[str] = None,
                 choices_provider: Optional[Callable[[SimulationContext], List[str]]] = None):
        self.key = key
        self.type = type_
        self.optional = optional
        self.default = default
        self.display_name = display_name
        self.choices_provider = choices_provider

    def get_value(self, value: str) -> T:
        percentage_match = re.match(r"(\d+)%", value)
        match self.type:
            case type_ if type_ == bool:
                if value:
                    return value.lower() in ["true", "1", "t", "y", "yes"]
                if self.optional:
                    return self.default
            case type_ if type_ == date:
                if value:
                    return date.fromisoformat(value)
                if self.optional:
                    return self.default
            case type_ if type_ == list:
                if value:
                    return value.split(",")
                if self.optional:
                    return self.default
            case type_ if type_ == float and percentage_match:
                return self.get_value(percentage_match.group(1)) / 100
            case type_:
                if value:
                    return type_(value)
                if self.optional:
                    return self.default

        raise UserError(f"Argument {self.get_display_name()} is not optional")

    def get_display_name(self) -> str:
        return self.display_name if self.display_name else self.key

    def stringify(self, value: T) -> str:
        return str(value)

    def load_value(self, context: SimulationContext) -> T:
        choices: Optional[List[str]] = self.choices_provider(
            context) if self.choices_provider else None
        if choices and self.optional:
            additional_brackets = " [" + ", ".join(
                map(self.stringify, choices)) + "; default: " + self.stringify(self.default) + "]"
        elif choices:
            additional_brackets = " [" + ", ".join(map(self.stringify, choices)) + "]"
        elif self.optional:
            additional_brackets = " [default: " + self.stringify(self.default) + "]"
        else:
            additional_brackets = ""
        value = input(
            f"{self.get_display_name()}{additional_brackets}: ")
        return self.get_value(value)


class SimulationTypeConfig:
    key: str
    display_name: Optional[str]
    type: Type
    arguments: List[CLIArgument]

    def __init__(self, name: str, display_name: Optional[str], type_: Type,
                 arguments: List[CLIArgument]):
        self.key = name
        self.display_name = display_name
        self.type = type_
        self.arguments = arguments

    def get_display_name(self) -> str:
        return self.display_name if self.display_name else self.key


class Config:
    investment: SimulationTypeConfig
    mortgage: SimulationTypeConfig
    building_society_savings_contract: SimulationTypeConfig
    overlay: SimulationTypeConfig

    def __init__(self):
        self.investment = SimulationTypeConfig(
            "investment",
            "Investment",
            InvestmentSimulation,
            [
                CLIArgument("start_date", date, True, date.today(), "Start Date"),
                CLIArgument("end_date", date, display_name="End Date"),
                CLIArgument("starting_capital", float, display_name="Starting Capital"),
                CLIArgument("monthly_investment", float, display_name="Monthly Investment"),
                CLIArgument("yearly_return", float, display_name="Yearly Return"),
            ]
        )
        self.mortgage = SimulationTypeConfig(
            "mortgage",
            "Mortgage",
            MortgageSimulation,
            [
                CLIArgument("start_date", date, True, date.today(), "Start date"),
                CLIArgument("end_date", date, display_name="End date"),
                CLIArgument("mortgage_sum", float, False, None,
                            "Mortgage Sum"),
                CLIArgument("downpayment_ratio", float, True, .2, "Downpayment ratio"),
                CLIArgument("interest_rate", float, display_name="Interest rate"),
                CLIArgument("monthly_payment", float, display_name="Monthly payment"),
            ]
        )
        self.building_society_savings_contract = SimulationTypeConfig(
            "building_savings_contract",
            "Building Society Savings Contract",
            BuildingSocietySavingsContract,
            [
                CLIArgument("start_date", date, True, date.today(), "Start date"),
                CLIArgument("end_date", date, display_name="End date"),
                CLIArgument("mortgage_activation_date", date,
                            display_name="Mortgage activation date"),
                CLIArgument("starting_capital", float, display_name="Starting capital"),
                CLIArgument("savings_rate", float, display_name="Savings rate"),
                CLIArgument("savings_interest", float, display_name="Savings interest"),
                CLIArgument("mortgage_interest", float, display_name="Mortgage interest"),
                CLIArgument("mortgage_pay_rate", float, optional=True,
                            display_name="Mortgage pay rate"),
                CLIArgument("savings_sum", float, display_name="Savings sum"),
            ]
        )
        self.overlay = SimulationTypeConfig(
            "overlay",
            "Overlay",
            Overlay,
            [
                CLIArgument("simulations", list, display_name="Simulations",
                            choices_provider=lambda context: [sim.get_short_identifier() for sim in
                                                              context.simulations]),
            ]
        )

    def get_simulation_types(self) -> List[SimulationTypeConfig]:
        return [
            self.investment,
            self.mortgage,
            self.building_society_savings_contract,
            self.overlay,
        ]

    def get_simulation_type(self, key: str) -> SimulationTypeConfig:
        try:
            return next(t for t in self.get_simulation_types() if t.key == key)
        except StopIteration:
            raise UserError(f"Simulation type {key} not found")
