"""Overlay simulation"""
from typing import List, Dict

import pandas as pd

from finance_macros.data_visualization import interpolate_data_nonlinear
from finance_macros.simulation.core import Simulation, SimulationContext


class Overlay(Simulation):
    """A special simulation that combines the results of multiple simulations."""
    simulations: List[Simulation]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 simulations: List[str]):
        super().__init__(export_directory, identifier, context)
        self.simulations = context.get_simulations_with_ids(*simulations)

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

    def get_column_names(self) -> List[str]:
        nameslist = [sim.get_column_names() for sim in self.simulations]
        return [col for sublist in nameslist for col in sublist]
