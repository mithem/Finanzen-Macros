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
        raise NotImplementedError

    def get_results(self) -> Dict:
        raise NotImplementedError

    def get_data(self) -> pd.DataFrame:
        results = self.get_results()
        dates = results["date"]
        del results["date"]
        df = pd.DataFrame(results, index=dates)
        df.index.set_names("date", inplace=True)
        return df

    def write_csv(self):
        self.get_data().to_csv(os.path.join(self.export_directory, self.identifier + ".csv"))

    @staticmethod
    def make_short_identifier(identifier):
        try:
            name, count = re.match(r"(.+)_(\d+)", identifier).groups()
            name_shorthand = "".join(map(lambda s: s[0], name.split("_")))
            return name_shorthand + count
        except AttributeError:  # No match
            return identifier

    def get_short_identifier(self):
        return self.make_short_identifier(self.identifier)


class SimulationContext:
    simulations: List[Simulation]

    def __init__(self, simulations: Optional[List[Simulation]] = None):
        if simulations:
            self.simulations = simulations
        else:
            self.simulations = []

    def add_simulation(self, simulation: Simulation):
        self.simulations.append(simulation)

    def get_simulations_with_id(self, identifier: str) -> List[Simulation]:
        short_id = Simulation.make_short_identifier(identifier)
        return list(
            filter(lambda s: s.identifier == identifier or s.get_short_identifier() == short_id,
                   self.simulations))


class TimeSeriesSimulation(Simulation):
    starting_date: datetime.date
    end_date: datetime.date
    _dates: List[datetime.date]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 starting_date: datetime.date,
                 end_date: datetime.date):
        super().__init__(export_directory, identifier, context)
        self.starting_date = starting_date
        self.end_date = end_date
        self._dates = [self.starting_date]

    def call_simulation_functions(self,
                                  daily_callback: Optional[Callable[[datetime.date], None]] = None,
                                  monthly_callback: Optional[
                                      Callable[[datetime.date], None]] = None,
                                  day_of_month: int = 1):
        date = self.starting_date
        while date < self.end_date:
            date += datetime.timedelta(days=1)
            if daily_callback:
                daily_callback(date)
            if monthly_callback and date.day == day_of_month:
                monthly_callback(date)
            if daily_callback or (monthly_callback and date.day == day_of_month):
                self._dates.append(date)


class Overlay(Simulation):
    simulations: List[Simulation]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 simulations: List[str]):
        super().__init__(export_directory, identifier, context)
        simulations = [context.get_simulations_with_id(identifier) for identifier in
                       simulations]
        self.simulations = [simulation for sublist in simulations for simulation in sublist]

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
            for key, values in result.items():
                if key != "date":
                    results[sim + "_" + key] = list(interpolated[key])

            if i == 0:
                results["date"] = list(interpolated["date"])
        return results


class UserError(Exception):
    pass


T = TypeVar("T")


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
