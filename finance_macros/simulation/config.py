"""Configuration for the CLI interface of the simulation module."""
import re
from datetime import date
from typing import Optional, Type, List, Callable, Generic, Dict, Any, Tuple

from finance_macros.simulation.core import T, UserError, SimulationContext


# pylint: disable=too-few-public-methods
class Parsable(Generic[T]):
    """Interface for objects that can be parsed from a input string."""

    @staticmethod
    def get_value(context: SimulationContext, input_str: str) -> T:
        """Parses the input string and returns the corresponding value."""
        raise NotImplementedError()


# pylint: disable=too-many-instance-attributes
class CLIArgument(Generic[T]):
    """A CLI argument. Used to generically define the arguments the CLI interface asks the user
    to fill in parameters for simulations."""
    key: str
    display_name: Optional[str]
    type: Type
    type_name: str
    optional: bool
    default: Optional[T]
    default_frontend_value: str
    choices_provider: Optional[Callable[[SimulationContext], List[str]]]
    additional_arg_provider: Optional[
        Callable[[SimulationContext, Optional[T]], List["CLIArgument"]]]

    # pylint: disable=too-many-arguments
    def __init__(self, key: str, type_: Type, optional: bool = False, default: Optional[T] = None,
                 display_name: Optional[str] = None,
                 choices_provider: Optional[Callable[[SimulationContext], List[str]]] = None,
                 additional_arg_provider: Optional[
                     Callable[[SimulationContext, Optional[T]], List["CLIArgument"]]] = None):
        self.key = key
        self.type = type_
        self.optional = optional
        self.default = default
        self.display_name = display_name
        self.choices_provider = choices_provider
        self.additional_arg_provider = additional_arg_provider
        self.calculate_default_frontend_value()
        self.calculate_type_name()
        CLIArgumentLibrary.register_argument(self)

    def __str__(self):
        return f"Argument('{self.key}', {self.type}, optional={self.optional})"

    # pylint: disable=too-many-return-statements
    def get_value(self, context: SimulationContext, value: str) -> Optional[T]:
        """Retrieves a valid value from the input string, applying type-dependent utilities (like
        %-signs for floats)."""
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
                    itemlistlist = [item.split(",") for item in value.split(", ")]
                    return [item for sublist in itemlistlist for item in sublist]  # type: ignore
                if self.optional:
                    return self.default
            case type_ if issubclass(type_, Parsable):
                if value:
                    return type_.get_value(context, value)  # type: ignore
                if self.optional:
                    return self.default
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
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    def load_value(self, context: SimulationContext,
                   value_provider: Optional[Callable[[str, "CLIArgument"], str]] = None) -> Tuple[
        Optional[T], List["CLIArgument"]]:
        """Prompt the user for the value of this argument and return it.
        :param context: The simulation context.
        :param value_provider: A function that prompts the user for a value and returns it."""

        def f_value_provider(prompt: str, _: CLIArgument) -> str:
            return input(prompt)

        if value_provider is None:
            value_provider = f_value_provider
        if issubclass(self.type, Promptable):
            type_ = self.type()
            return type_.prompt(context, value_provider), []
        prompt = self.get_user_prompt(context)
        usr_input = value_provider(
            prompt, self)
        value = self.get_value(context, usr_input)
        additional_args = self.additional_arg_provider(
            context,
            value
        ) if self.additional_arg_provider else []
        return value, additional_args

    def get_user_prompt(self, context: SimulationContext) -> str:
        """Return the string to prompt the user with."""
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
        return f"{self.get_display_name()}{additional_brackets}: "

    def calculate_default_frontend_value(self):
        """Calculates the default frontend value and saves it for the frontend."""
        if self.default is None:
            self.default_frontend_value = ""
        else:
            self.default_frontend_value = self.stringify(self.default)

    def calculate_type_name(self):
        """Calculates the type name and saves it for the frontend."""
        match self.type:
            case type_ if type_ == bool:
                self.type_name = "bool"
            case type_ if type_ == date:
                self.type_name = "date"
            case type_ if type_ == Float:
                self.type_name = "float"
            case type_ if issubclass(type_, Parsable):
                self.type_name = type_.__name__
            case type_ if type_ == str:
                self.type_name = "string"
            case type_ if issubclass(type_, Promptable):
                self.type_name = f"<Promptable type=\"{self.type.__name__}\"/>"
            case type_:
                self.type_name = type_.__name__

    def __eq__(self, other):
        return (
                isinstance(other, CLIArgument)
                and self.key == other.key
                and self.type == other.type
                and self.optional == other.optional
                and self.default == other.default
                and self.display_name == other.display_name
        )


class CLIArgumentLibrary:
    """The library of supported CLI arguments."""
    _arguments: Dict[str, CLIArgument] = {}

    @staticmethod
    def register_argument(argument: CLIArgument):
        """Registers an argument in the library."""
        filtered = list(
            filter(lambda arg: arg.key == argument.key, CLIArgumentLibrary._arguments.values()))
        if filtered and filtered[0] != argument:
            raise UserError(f"Argument with key '{argument.key}' already registered.")
        CLIArgumentLibrary._arguments[argument.key] = argument

    @staticmethod
    def get_argument(key: str) -> CLIArgument:
        """Returns the argument with the specified key."""
        return CLIArgumentLibrary._arguments[key]


class Promptable(Generic[T]):
    """Interface for objects that can be prompted for a value."""
    args: List[CLIArgument]

    def __init__(self, args: Optional[List[CLIArgument]] = None):
        if args is None:
            self.args = []
        else:
            self.args = args

    def prepare_args(self, context: SimulationContext):
        """Prepare the arguments for the prompt."""

    def prompt(self, context: SimulationContext,
               value_provider: Callable[[str, CLIArgument], str] = lambda prompt, _: input(
                   prompt)) -> T:
        """Returns a dictionary of the arguments."""
        self.prepare_args(context)
        queue = self.args.copy()
        args: Dict[str, Any] = {}
        while queue:
            arg = queue.pop(0)
            value, extra_args = arg.load_value(context, value_provider)
            args[arg.key] = value
            queue.extend(extra_args)

        values = self.process_values(context, args)
        return values

    # pylint: disable=unused-argument
    def process_values(self, context: SimulationContext, values: Dict[str, Any]) -> T:
        """Processes the values and returns the final object."""
        return values  # type: ignore


# pylint: disable=too-few-public-methods
class SimulationTypeConfig(Promptable):
    """Configuration for a simulation type (like investment or mortgage)."""
    key: str
    display_name: Optional[str]
    type: Type

    def __init__(self, name: str, display_name: Optional[str], type_: Type,
                 arguments: List[CLIArgument]):
        super().__init__(arguments)
        self.key = name
        self.display_name = display_name
        self.type = type_

    def get_display_name(self) -> str:
        """Returns the display name of the simulation type, or the key if no display name is set."""
        return self.display_name if self.display_name else self.key


class Float(Parsable):
    """A float that can be parsed from a string."""

    @staticmethod
    def get_value(context: SimulationContext, input_str: str) -> float:
        match = re.match(r"(\d+((.|,)\d+)?)%", input_str)
        if match:
            return float(match.group(1)) / 100
        return float(input_str)


def cli_arg_end_date(prefix: str,
                     additional_arg_provider: Optional[
                         Callable[[SimulationContext, Any], List[CLIArgument]]] = None):
    """:return: CLI argument for the end date of a simulation."""
    return CLIArgument(prefix + "_end_date", date, True, None, "End Date",
                       additional_arg_provider=additional_arg_provider)


class Config:
    """Configuration for the CLI interface."""
    investment: SimulationTypeConfig
    mortgage: SimulationTypeConfig
    building_society_savings_contract: SimulationTypeConfig
    overlay: SimulationTypeConfig
    combination: SimulationTypeConfig
    real_estate: SimulationTypeConfig

    def __init__(self):
        # import here as otherwise, there would be a circular import
        # pylint: disable=import-outside-toplevel
        from finance_macros.simulation.combination import Combination, CombinationFunctionList
        from finance_macros.simulation.investment import InvestmentSimulation
        from finance_macros.simulation.mortgage import MortgageSimulation
        from finance_macros.simulation.overlay import Overlay
        from finance_macros.simulation.building_society_savings_contract import \
            BuildingSocietySavingsContract
        from finance_macros.simulation.real_estate import RealEstateSimulation
        start_date = CLIArgument("start_date", date, True, date.today(), display_name="Start Date")
        self.investment = SimulationTypeConfig(
            "investment",
            "Investment",
            InvestmentSimulation,
            [
                start_date,
                cli_arg_end_date("i",
                                 lambda _, value: (
                                     [CLIArgument(
                                         "i_target_capital",
                                         Float,
                                         display_name="Target Capital")] if value is None else [])
                                 ),
                CLIArgument("i_starting_capital", Float, display_name="Starting Capital"),
                CLIArgument("i_monthly_investment", Float, display_name="Monthly Investment"),
                CLIArgument("i_yearly_return", Float, display_name="Yearly Return"),
            ]
        )
        self.mortgage = SimulationTypeConfig(
            "mortgage",
            "Mortgage",
            MortgageSimulation,
            [
                start_date,
                cli_arg_end_date("m"),
                CLIArgument("m_mortgage_sum", Float, False, None,
                            "Mortgage Sum"),
                CLIArgument("m_downpayment_ratio", Float, True, .2, "Downpayment ratio"),
                CLIArgument("m_interest_rate", Float, display_name="Interest rate"),
                CLIArgument("m_monthly_payment", Float, display_name="Monthly payment"),
            ]
        )
        self.building_society_savings_contract = SimulationTypeConfig(
            "building_savings_contract",
            "Building Society Savings Contract",
            BuildingSocietySavingsContract,
            [
                start_date,
                CLIArgument("bsc_contract_sum", Float, display_name="Contract sum"),
                CLIArgument("bsc_starting_capital", Float, display_name="Starting capital"),
                CLIArgument("bsc_savings_rate", Float, display_name="Savings rate"),
                CLIArgument("bsc_savings_interest", Float, display_name="Savings interest"),
                CLIArgument("bsc_mortgage_interest", Float, display_name="Mortgage interest"),
                CLIArgument("bsc_mortgage_pay_rate", Float, optional=True,
                            display_name="Mortgage pay rate"),
                CLIArgument("bsc_mortgage_downpayment_ratio", Float, False, .2, "Downpayment ratio")
            ]
        )
        self.overlay = SimulationTypeConfig(
            "overlay",
            "Overlay",
            Overlay,
            [
                CLIArgument("o_simulations", list, display_name="Simulations",
                            choices_provider=lambda context: context.get_short_identifiers())
            ]
        )
        self.combination = SimulationTypeConfig(
            "combination",
            "Combination",
            Combination,
            [
                CLIArgument("c_functions", CombinationFunctionList, display_name="Functions",
                            additional_arg_provider=CombinationFunctionList.additional_arg_provider)
            ]
        )
        self.real_estate = SimulationTypeConfig(
            "real_estate",
            "Real Estate",
            RealEstateSimulation,
            [
                start_date,
                CLIArgument("re_buy_price", Float, display_name="Buy price"),
                CLIArgument("re_cash_available", Float, display_name="Cash available"),
                CLIArgument("re_pay_rate", Float, display_name="Pay rate"),
                CLIArgument("re_rent", Float, display_name="Rent"),
                CLIArgument("re_investment_return", Float, display_name="Investment return"),
                CLIArgument("re_mortgage_interest", Float, display_name="Mortgage interest"),
                CLIArgument("re_target_downpayment", Float, display_name="Target downpayment")
            ]
        )

    def get_simulation_types(self) -> List[SimulationTypeConfig]:
        """Returns a list of all simulation types."""
        return [
            self.investment,
            self.mortgage,
            self.building_society_savings_contract,
            self.overlay,
            self.combination,
            self.real_estate
        ]

    def get_simulation_type(self, key: str) -> SimulationTypeConfig:
        """Returns the simulation type with the given key."""
        sim_types = self.get_simulation_types()
        try:
            return next(t for t in sim_types if t.key == key)
        except StopIteration as exc:
            types = [f"{type_.display_name} ({type_.key})" for type_ in sim_types]
            raise UserError(
                f"Simulation type '{key}' not found. Available are: {', '.join(types)}.") from exc
