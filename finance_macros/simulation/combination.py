"""Simulation combining multiple different ones."""
import re
from enum import Enum
from typing import List, Dict, Any

from finance_macros.simulation.config import Promptable, CLIArgument, Parsable
from finance_macros.simulation.core import Simulation, SimulationContext
from finance_macros.simulation.overlay import Overlay


class CombinationOperation(Enum):
    """An operation to apply to the results of the simulations."""
    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4
    MODULO = 5
    INT_DIVIDE = 6

    @staticmethod
    # pylint: disable=unused-argument
    def choices_provider(context: SimulationContext) -> List[str]:
        """Returns the choices for the CLI."""
        return [operation.name for operation in CombinationOperation]

    def __str__(self):
        match self:
            case CombinationOperation.ADD:
                return "+"
            case CombinationOperation.SUBTRACT:
                return "-"
            case CombinationOperation.MULTIPLY:
                return "*"
            case CombinationOperation.DIVIDE:
                return "/"
            case CombinationOperation.MODULO:
                return "%"
            case CombinationOperation.INT_DIVIDE:
                return "//"
            case other:
                raise ValueError(f"Invalid operation: {other}")


# pylint: disable=too-few-public-methods
class CombinationOperationParser(Parsable):
    """Parser for `CombinationOperation`"""

    @staticmethod
    def get_value(context: SimulationContext, input_str: str) -> "CombinationOperation":
        match input_str.lower():
            case "add" | "+" | "plus":
                return CombinationOperation.ADD
            case "subtract" | "-" | "minus":
                return CombinationOperation.SUBTRACT
            case "multiply" | "*" | "times":
                return CombinationOperation.MULTIPLY
            case "divide" | "/" | "divided by":
                return CombinationOperation.DIVIDE
            case "modulo" | "%" | "mod":
                return CombinationOperation.MODULO
            case "int_divide" | "//" | "int_divided by":
                return CombinationOperation.INT_DIVIDE
            case other:
                raise ValueError(f"Invalid operation: {other}")


class Combination(Simulation):
    """A special simulation that combines the results of one or multiple simulations, not by
    overlaying, but applying functions to the simulation's columns, including calculating new
    columns based on different simulations."""

    class CombinationFunction(Parsable):
        """A function applying to one or more simulations' columns. Simulations specify which
        simulations' columns to use, and the operation specifies how to combine them. A simulation
        can be included multiple times, and the operation can be applied to multiple columns of that
        same simulation. In any case, the length of the simulations and columns lists must be the
        same."""
        operation: CombinationOperation
        simulations: List[Simulation]
        columns: List[str]

        def __init__(self, key: str, operation: CombinationOperation, simulations: List[Simulation],
                     columns: List[str]):
            self.key = key
            self.operation = operation
            self.simulations = simulations
            self.columns = columns
            assert len(self.simulations) == len(
                self.columns), "Length of simulations and columns must be the same"

        @staticmethod
        def get_value(context: SimulationContext,
                      input_str: str) -> "Combination.CombinationFunction":
            pattern = r"(?P<sim1>[\w\d]+)\.(?P<key1>[\w\d]+) ?(?P<operation>.{1,4}?) ?\
(?P<sim2>[\w\d]+)\.(?P<key2>[\w\d]+)"
            match = re.match(pattern, input_str)
            if match:
                sim1 = match.group("sim1")
                key1 = match.group("key1")
                operation = match.group("operation")
                sim2 = match.group("sim2")
                key2 = match.group("key2")
                sims = context.get_simulations_with_ids(sim1, sim2)
                operation = CombinationOperationParser.get_value(context, operation)
                return Combination.CombinationFunction(
                    key1 + str(operation) + key2,
                    operation,
                    sims,
                    [key1, key2]
                )
            raise ValueError(f"Can't interpret '{input_str}' as a combination function.")

        def evaluate(self, results: Dict) -> Dict:
            """Evaluate the function on the results."""
            data = results.copy()
            data[self.key] = data[
                self.simulations[0].get_short_identifier() + "_" + self.columns[0]].copy()
            if len(self.simulations) == 1:
                return data
            for i in range(1, len(self.simulations)):
                simulation = self.simulations[i]
                short_id = simulation.get_short_identifier()
                column = short_id + "_" + self.columns[i]
                for j in range(len(data[self.key])):
                    match self.operation:
                        case CombinationOperation.ADD:
                            data[self.key][j] += \
                                data[column][j]
                        case CombinationOperation.SUBTRACT:
                            data[self.key][j] -= \
                                data[column][j]
                        case CombinationOperation.MULTIPLY:
                            data[self.key][j] *= \
                                data[column][j]
                        case CombinationOperation.DIVIDE:
                            data[self.key][j] /= \
                                data[column][j]
                        case CombinationOperation.MODULO:
                            data[self.key][j] %= \
                                data[column][j]
                        case CombinationOperation.INT_DIVIDE:
                            data[self.key][j] //= \
                                data[column][j]
                        case other:
                            raise ValueError(f"Invalid operation {other}.")
            return data

    functions: List[CombinationFunction]
    overlay: Overlay

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 functions: List[CombinationFunction]):
        super().__init__(export_directory, identifier, context)
        self.functions = functions
        simulationslist = [function.simulations for function in self.functions]
        sims = [sim.get_short_identifier() for sublist in simulationslist for sim in sublist]
        self.overlay = Overlay(export_directory, identifier, context, sims)

    def simulate(self):
        self.overlay.simulate()

    def get_results(self) -> Dict:
        results = self.overlay.get_results()
        for function in self.functions:
            results = function.evaluate(results)
        return results

    def get_column_names(self) -> List[str]:
        return [function.key for function in self.functions] + self.overlay.get_column_names()


class CombinationFunctionList(Promptable):
    """A list of combination functions used for CLI configuration."""
    functions: List[Combination.CombinationFunction]

    def __init__(self):
        args = [
            CLIArgument("function_count", int, display_name="Number of functions",
                        additional_arg_provider=self.additional_arg_provider),
        ]
        super().__init__(args)
        self.functions = []

    @staticmethod
    def additional_arg_provider(context: SimulationContext, value) -> List[CLIArgument]:
        """The additional arg provider callback for the function count argument."""
        column_specifications = []
        for simulation in context.simulations:
            for column in simulation.get_column_names():
                column_specifications.append(simulation.get_short_identifier() + "." + column)
        args: List[CLIArgument] = [
            CLIArgument("function_specification_" + str(i + 1), Combination.CombinationFunction,
                        choices_provider=lambda _: column_specifications)
            for i in range(value)
        ]
        return args

    def process_values(self, context: SimulationContext, values: Dict[str, Any]) -> List[
        Combination.CombinationFunction]:
        self.functions = []
        for i in range(values["function_count"]):
            self.functions.append(values["function_specification_" + str(i + 1)])
        return self.functions
