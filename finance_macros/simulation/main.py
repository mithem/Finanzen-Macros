"""Main entrypoint for the simulation module. This module is responsible for running the simulation
and the dashboard."""
import argparse
import os

from finance_macros.simulation import export_viewer
from finance_macros.simulation.config import Config
from finance_macros.simulation.core import SimulationContext, Simulation, Colors

CONFIG = Config()


def run_simulation(context: SimulationContext, simulation_type: str, export_directory: str):
    """Run a simulation with arguments prompted from the user.
    :param context: The simulation context
    :param simulation_type: The type of simulation to run
    :param export_directory: The directory to export the simulation to
    """
    config = CONFIG.get_simulation_type(simulation_type)
    print(f"{config.get_display_name()} simulation:")
    args = config.prompt(context)
    sim: Simulation = config.type(identifier=simulation_type,
                                  export_directory=export_directory,
                                  context=context,
                                  **args)
    context.add_simulation(sim)
    sim.simulate()
    sim.write_csv()
    print(
        f"Saved simulation under {sim.identifier} ({sim.get_short_identifier()}) \
{Colors.OKGREEN}\u2713{Colors.ENDC}")


def delete_existing(export_directory: str):
    """Delete existing data."""
    data = export_viewer.load_data(export_directory)
    for simulation_type in data.keys():  # pylint: disable=consider-iterating-dictionary
        os.remove(os.path.join(export_directory, simulation_type + ".csv"))
    print(f"Deleted all existing simulations from '{export_directory}': {', '.join(data.keys())}.")


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description="Run a financial simulation")
    parser.add_argument("--add-simulation", "-a", "--simulation", "-s", type=str,
                        help="Add a simulation type", nargs="+", action="append")
    parser.add_argument("--export-directory", "-e", type=str, required=True,
                        help="Export directory")
    parser.add_argument("--dashboard-only", "-do", action="store_true",
                        help="Only run the dashboard (not any new simulations)")
    parser.add_argument("--delete-existing", "-de", action="store_true",
                        help="Delete existing data")
    args = parser.parse_args()
    if args.delete_existing:
        delete_existing(args.export_directory)
    context = SimulationContext()
    if not args.dashboard_only:
        if args.add_simulation:
            for simulation_type in args.add_simulation:
                assert len(simulation_type) == 1, "Only one simulation type can be added at a time"
                run_simulation(context, simulation_type[0], args.export_directory)
        else:
            parser.print_help()

    export_viewer.run(args.export_directory)


if __name__ == "__main__":
    main()
