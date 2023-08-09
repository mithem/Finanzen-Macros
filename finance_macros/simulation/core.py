"""Core components for financial simulations"""
import datetime
import os
import re
from typing import Callable, List, Dict, Optional, TypeVar

import pandas as pd

from finance_macros.data_visualization import interpolate_data_nonlinear


class Simulation:
    """Base class for financial simulations"""
    export_directory: str
    identifier: str

    def __init__(self, export_directory: str, identifier: str, context):
        self.export_directory = export_directory
        self.identifier = identifier
        self.context = context

    def simulate(self):
        """Run the simulation, saving its state only in the simulation object itself."""
        raise NotImplementedError

    def get_results(self) -> Dict:
        """:returns: results of the simulation as a dictionary, including a date column."""
        raise NotImplementedError

    def get_data(self) -> pd.DataFrame:
        """:returns: Results of the simulation on the basis of the `get_results()` method."""
        results = self.get_results()
        dates = results["date"]
        del results["date"]
        data = pd.DataFrame(results, index=dates)
        data.index.set_names("date", inplace=True)
        return data

    def write_csv(self):
        """Write the results of the simulation to a CSV file specified by the export directory and
        the simulation identifier."""
        self.get_data().to_csv(os.path.join(self.export_directory, self.identifier + ".csv"))

    @staticmethod
    def make_short_identifier(identifier: str):
        """:param identifier: the identifier of a simulation
        :returns: the short identifier for the simulation, based on the identifier given to the
        simulation."""
        match = re.match(r"(.+)_(\d+)", identifier)
        if not match:
            return identifier
        name, count = match.groups()
        name_shorthand = "".join(map(lambda s: s[0], name.split("_")))
        return name_shorthand + count

    def get_short_identifier(self):
        """:returns: the short identifier for this simulation."""
        return self.make_short_identifier(self.identifier)


class SimulationContext:
    """Context containing useful/necessary information for (some) simulations."""
    simulations: List[Simulation]

    def __init__(self, simulations: Optional[List[Simulation]] = None):
        if simulations:
            self.simulations = simulations
        else:
            self.simulations = []

    def add_simulation(self, simulation: Simulation):
        """Add a simulation to the context.
        :param simulation: the simulation to add to the context."""
        self.simulations.append(simulation)

    def get_simulations_with_id(self, identifier: str) -> List[Simulation]:
        """Get all simulations with a given identifier.
        :param identifier: the identifier to search for.
        :returns: all simulations with the given identifier."""
        short_id = Simulation.make_short_identifier(identifier)
        return list(
            filter(lambda s: s.identifier == identifier or s.get_short_identifier() == short_id,
                   self.simulations))


# pylint: disable=abstract-method
class TimeSeriesSimulation(Simulation):
    """Base class for simulations that are run over a period of time."""
    start_date: datetime.date
    end_date: datetime.date
    _dates: List[datetime.date]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 starting_date: datetime.date,
                 end_date: datetime.date):
        super().__init__(export_directory, identifier, context)
        self.start_date = starting_date
        self.end_date = end_date
        self._dates = [self.start_date]

    def call_simulation_functions(self,
                                  daily_callback: Optional[Callable[[datetime.date], None]] = None,
                                  monthly_callback: Optional[
                                      Callable[[datetime.date], None]] = None,
                                  day_of_month: int = 1):
        """Call the given callbacks on each day and/or each month.
        :param daily_callback: the function to call on each day.
        :param monthly_callback: the function to call on each month.
        :param day_of_month: the day of the month on which to call the monthly callback."""
        date = self.start_date
        while date < self.end_date:
            date += datetime.timedelta(days=1)
            if daily_callback:
                daily_callback(date)
            if monthly_callback and date.day == day_of_month:
                monthly_callback(date)
            if daily_callback or (monthly_callback and date.day == day_of_month):
                self._dates.append(date)


class Overlay(Simulation):
    """A special simulation that combines the results of multiple simulations."""
    simulations: List[Simulation]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 simulations: List[str]):
        super().__init__(export_directory, identifier, context)
        simlistlist = [context.get_simulations_with_id(identifier) for identifier in
                       simulations]
        self.simulations = [simulation for sublist in simlistlist for simulation in sublist]

    def simulate(self):
        for simulation in self.simulations:
            simulation.simulate()

    def get_results(self) -> Dict:
        tmp = {}
        for simulation in self.simulations:
            tmp[simulation.get_short_identifier()] = simulation.get_results()
        results = {}
        start_date = min(
            map(lambda sim: sim["date"][0], tmp.values()))
        end_date = max(
            map(lambda sim: sim["date"][-1], tmp.values()))
        for i, (sim, result) in enumerate(tmp.items()):
            interpolated = interpolate_data_nonlinear(pd.DataFrame(result), "date", start_date,
                                                      end_date)
            for key, values in interpolated.items():
                if key != "date":
                    results[sim + "_" + key] = list(values)

            if i == 0:
                results["date"] = list(interpolated["date"])
        return results


class UserError(Exception):
    """An error that is caused by the user, not by the program."""


T = TypeVar("T")


# pylint: disable=too-few-public-methods
class Colors:
    """ANSI colors for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
