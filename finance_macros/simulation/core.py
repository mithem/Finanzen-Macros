"""Core components for financial simulations"""
import datetime
import os
import re
from typing import Callable, List, Dict, Optional, TypeVar

import pandas as pd

CSV_FILE_COUNT_PER_SIM_TYPE = {}


class Simulation:
    """Base class for financial simulations"""
    export_directory: str
    identifier: str
    context: "SimulationContext"

    def __init__(self, export_directory: str, identifier: str, context: "SimulationContext",
                 automatic_identifier_counting: bool = True):
        if automatic_identifier_counting:
            id_counter = CSV_FILE_COUNT_PER_SIM_TYPE.get(identifier, 1)
            CSV_FILE_COUNT_PER_SIM_TYPE[identifier] = id_counter + 1
            identifier_str = identifier + "_" + str(id_counter)
        else:
            identifier_str = identifier
        self.export_directory = export_directory
        self.identifier = identifier_str
        self.context = context
        self.context.add_simulation(self)

    def simulate(self):
        """Run the simulation, saving its state only in the simulation object itself."""
        raise NotImplementedError

    def get_column_names(self) -> List[str]:
        """:returns: list of column names of the results of the simulation, which is identical to \
        the results' keys."""
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
        match = re.match(r"(.+)_(\d+)(-(.+))?", identifier)
        if not match:
            return identifier
        groups = match.groups()
        name = groups[0]
        count = groups[1]
        try:
            extra_info = groups[3]
        except IndexError:
            extra_info = None
        name_shorthand = "".join(map(lambda s: s[0], name.split("_")))
        return name_shorthand + count + (("-" + extra_info) if extra_info else "")

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
        if not simulation.identifier in map(lambda sim: sim.identifier, self.simulations):
            self.simulations.append(simulation)

    def get_simulations_with_ids(self, *identifiers: str) -> List[Simulation]:
        """Get all simulations with one of the given identifiers.
        :param identifiers: the identifiers to search for.
        :returns: all simulations with the given identifier."""
        results = []
        for identifier in identifiers:
            results += list(filter(
                lambda s: s.identifier == identifier or s.get_short_identifier() == identifier,
                self.simulations))
        return results

    def get_short_identifiers(self) -> List[str]:
        """:returns: the short identifiers of all simulations in the context."""
        return list(map(lambda s: s.get_short_identifier(), self.simulations))

    def reset(self):
        """Reset the context to its initial state."""
        self.simulations = []


# pylint: disable=abstract-method
class TimeSeriesSimulation(Simulation):
    """Base class for simulations that are run over a period of time."""
    start_date: datetime.date
    end_date: Optional[datetime.date]
    d_dates: List[datetime.date]

    end_condition_achieved_callback: Optional[Callable[[datetime.date], bool]]

    # pylint: disable=too-many-arguments
    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 starting_date: datetime.date,
                 end_date: Optional[datetime.date] = None,
                 end_condition_achieved_callback: Optional[
                     Callable[[datetime.date], bool]] = None,
                 automatic_identifier_counting: bool = True):
        super().__init__(export_directory, identifier, context, automatic_identifier_counting)
        assert end_date or end_condition_achieved_callback, "Either an end date or an end \
        condition achieved callback must be given to calculate an appropriate end date."
        self.start_date = starting_date
        self.end_date = end_date
        self.reset_time_series_data()

        self.end_condition_achieved_callback = end_condition_achieved_callback

    def reset_time_series_data(self):
        self.d_dates = [self.start_date]

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
        while self.end_date is None or date < self.end_date:
            date += datetime.timedelta(days=1)
            if daily_callback:
                daily_callback(date)
            if monthly_callback and date.day == day_of_month:
                monthly_callback(date)
            if daily_callback or (monthly_callback and date.day == day_of_month):
                self.d_dates.append(date)
            if self.end_condition_achieved_callback:
                if self.end_condition_achieved_callback(date):
                    self.end_date = date


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
