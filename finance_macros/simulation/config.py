"""Configuration for the CLI interface of the simulation module."""
import re
from datetime import date
from typing import Optional, Type, List, Callable, Generic

from finance_macros.simulation.building_society_savings_contract import \
    BuildingSocietySavingsContract
from finance_macros.simulation.core import T, UserError, Overlay, SimulationContext
from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation


class CLIArgument(Generic[T]):
    """A CLI argument. Used to generically define the arguments the CLI interface asks the user
    to fill in parameters for simulations."""
    key: str
    display_name: Optional[str]
    type: Type
    optional: bool
    default: Optional[T]
    choices_provider: Optional[Callable]

    # pylint: disable=too-many-arguments
    def __init__(self, key: str, type_: Type, optional: bool = False, default: Optional[T] = None,
                 display_name: Optional[str] = None,
                 choices_provider: Optional[Callable[[SimulationContext], List[str]]] = None):
        self.key = key
        self.type = type_
        self.optional = optional
        self.default = default
        self.display_name = display_name
        self.choices_provider = choices_provider

    # pylint: disable=too-many-return-statements
    def get_value(self, value: str) -> Optional[T]:
        """Retrieves a valid value from the input string, applying type-dependent utilities (like
        %-signs for floats)."""
        percentage_match = re.match(r"(\d+)%", value)
        match self.type:
            case type_ if type_ == bool:
                if value:
                    return value.lower() in ["true", "1", "t", "y", "yes"]  # type: ignore
                if self.optional:
                    return self.default
            case type_ if type_ == date:
                if value:
                    return date.fromisoformat(value)  # type: ignore
                if self.optional:
                    return self.default
            case type_ if type_ == list:
                if value:
                    return value.split(",")  # type: ignore
                if self.optional:
                    return self.default
            case type_ if type_ == float and percentage_match:
                return self.get_value(percentage_match.group(1)) / 100  # type: ignore
            case type_:
                if value:
                    return type_(value)
                if self.optional:
                    return self.default

        raise UserError(f"Argument {self.get_display_name()} is not optional")

    def get_display_name(self) -> str:
        """Returns the display name of the argument, or the key if no display name is set."""
        return self.display_name if self.display_name else self.key

    def stringify(self, value: Optional[T]) -> str:
        """Returns a string representation of the value."""
        return str(value)

    def load_value(self, context: SimulationContext) -> Optional[T]:
        """Prompt the user for the value of this argument and return it."""
        choices: Optional[List[str]] = self.choices_provider(
            context) if self.choices_provider else None
        if choices and self.optional:
            additional_brackets = " [" + ", ".join(
                map(self.stringify, choices)) + "; default: " + self.stringify(  # type: ignore
                self.default) + "]"
        elif choices:
            additional_brackets = " [" + ", ".join(
                map(self.stringify, choices)) + "]"  # type: ignore
        elif self.optional:
            additional_brackets = " [default: " + self.stringify(self.default) + "]"
        else:
            additional_brackets = ""
        value = input(
            f"{self.get_display_name()}{additional_brackets}: ")
        return self.get_value(value)


# pylint: disable=too-few-public-methods
class SimulationTypeConfig:
    """Configuration for a simulation type (like investment or mortgage)."""
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
        """Returns the display name of the simulation type, or the key if no display name is set."""
        return self.display_name if self.display_name else self.key


class Config:
    """Configuration for the CLI interface."""
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
        """Returns a list of all simulation types."""
        return [
            self.investment,
            self.mortgage,
            self.building_society_savings_contract,
            self.overlay,
        ]

    def get_simulation_type(self, key: str) -> SimulationTypeConfig:
        """Returns the simulation type with the given key."""
        try:
            return next(t for t in self.get_simulation_types() if t.key == key)
        except StopIteration as exc:
            raise UserError(f"Simulation type {key} not found") from exc
