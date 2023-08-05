import argparse
from datetime import date

from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation

SIMULATION_TYPE_CONFIG = {
    "investment": {
        "type": InvestmentSimulation,
        "args": [("start_date", date), ("end_date", date), ("starting_capital", float),
                 ("monthly_investment", float), ("yearly_return", float)]
    },
    "mortgage": {
        "type": MortgageSimulation,
        "args": [("start_date", date), ("end_date", date), ("mortgage_sum", float),
                 ("downpayment_ratio", float), ("interest_rate", float),
                 ("monthly_payment", float)]
    }
}

CSV_FILE_COUNT_PER_SIM_TYPE = {}

for type in SIMULATION_TYPE_CONFIG:
    CSV_FILE_COUNT_PER_SIM_TYPE[type] = 1


def _get_value(value: str, type_):
    if type_ == date:
        return date.fromisoformat(value)
    return type_(value)


def run_simulation(simulation_type: str, export_directory: str):
    config = SIMULATION_TYPE_CONFIG[simulation_type]
    args = {}
    for name, type_ in config["args"]:
        args[name] = _get_value(input(f"{name}: "), type_)
    sim = config["type"](export_directory=export_directory, **args)
    sim.simulate()
    sim.write_csv(
        f"{simulation_type}_simulation_{CSV_FILE_COUNT_PER_SIM_TYPE[simulation_type]}.csv")
    CSV_FILE_COUNT_PER_SIM_TYPE[simulation_type] += 1


def main():
    parser = argparse.ArgumentParser(description="Run a financial simulation")
    parser.add_argument("--add-simulation", "-a", "--simulation", "-s", type=str,
                        help="Add a simulation type", nargs="+", action="append")
    parser.add_argument("--export-directory", "-e", type=str, required=True,
                        help="Export directory")
    args = parser.parse_args()
    if args.add_simulation:
        for simulation_type in args.add_simulation:
            assert len(simulation_type) == 1, "Only one simulation type can be added at a time"
            run_simulation(simulation_type[0], args.export_directory)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
