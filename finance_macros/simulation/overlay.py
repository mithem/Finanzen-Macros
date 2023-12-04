"""Overlay simulation"""
from typing import List, Dict, Union

import pandas as pd

from finance_macros.data_visualization import interpolate_data_nonlinear
from finance_macros.simulation.core import Simulation, SimulationContext


class Overlay(Simulation):
    """A special simulation that combines the results of multiple simulations."""
    simulations: List[Simulation]

    def __init__(self, export_directory: str, identifier: str, context: SimulationContext,
                 o_simulations: Union[List[str], List[Simulation]],
                 automatic_identifier_counting: bool = True):
        super().__init__(export_directory, identifier, context, automatic_identifier_counting)
        sims: List[Simulation] = []
        if isinstance(o_simulations[0], str):
            sims = context.get_simulations_with_ids(*o_simulations)
        elif isinstance(o_simulations[0], Simulation):
            sims = o_simulations  # type: ignore
        self.simulations = sims

    def simulate(self):
        for simulation in self.simulations:
            simulation.simulate()

    def get_results(self) -> Dict:
        tmp = {}
        for simulation in self.simulations:
            tmp[simulation.get_short_identifier()] = simulation.get_results()
        if len(tmp) == 0:
            raise ValueError("No simulations to overlay.")
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
        return [col for sim in self.simulations for col in sim.get_column_names()]
