"""Main entrypoint for the simulation module. This module is responsible for running the simulation
and the dashboard."""
import argparse

from finance_macros.simulation import server
from finance_macros.simulation.config import Config
from finance_macros.simulation.core import SimulationContext, Simulation, Colors

CSV_FILE_COUNT_PER_SIM_TYPE = {}
CONFIG = Config()

for type_ in CONFIG.get_simulation_types():
    CSV_FILE_COUNT_PER_SIM_TYPE[type_.key] = 1


def run_simulation(context: SimulationContext, simulation_type: str, export_directory: str):
    """Run a simulation with arguments prompted from the user.
    :param context: The simulation context
    :param simulation_type: The type of simulation to run
    :param export_directory: The directory to export the simulation to
    """
    config = CONFIG.get_simulation_type(simulation_type)
    count = CSV_FILE_COUNT_PER_SIM_TYPE[simulation_type]
    print(f"\n{config.display_name} simulation {count}:")
    args = config.prompt(context)
    identifier = f"{simulation_type}_{count}"
    sim: Simulation = config.type(identifier=identifier, export_directory=export_directory,
                                  context=context,
                                  **args)
    context.add_simulation(sim)
    sim.simulate()
    sim.write_csv()
    print(
        f"Saved simulation under {sim.identifier} ({sim.get_short_identifier()}) \
{Colors.OKGREEN}\u2713{Colors.ENDC}")
    CSV_FILE_COUNT_PER_SIM_TYPE[simulation_type] += 1


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description="Run a financial simulation")
    parser.add_argument("--add-simulation", "-a", "--simulation", "-s", type=str,
                        help="Add a simulation type", nargs="+", action="append")
    parser.add_argument("--export-directory", "-e", type=str, required=True,
                        help="Export directory")
    parser.add_argument("--dashboard-only", "-do", action="store_true",
                        help="Only run the dashboard (not any new simulations)")
    args = parser.parse_args()
    context = SimulationContext()
    if not args.dashboard_only:
        if args.add_simulation:
            for simulation_type in args.add_simulation:
                assert len(simulation_type) == 1, "Only one simulation type can be added at a time"
                run_simulation(context, simulation_type[0], args.export_directory)
        else:
            parser.print_help()

    server.run(args.export_directory)


if __name__ == "__main__":
    main()