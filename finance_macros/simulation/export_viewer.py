"""Dash server for visualizing simulation results."""
import os
import re
from typing import Dict

import pandas as pd
from dash import Dash, dcc, html

from finance_macros.simulation import graphs
from finance_macros.simulation.config import Config

CONFIG = Config()

app = Dash(__name__)
app.title = "Finance Simulation"


def run(export_directory: str):
    """Run the server."""
    data = load_data(export_directory)
    app.layout = get_layout(data)
    app.run_server()


def load_data(export_directory: str) -> dict[str, pd.DataFrame]:
    """Load simulation data from export directory."""
    files = list(filter(lambda f: any(f.startswith(sim_type.key + "_") for sim_type in
                                      CONFIG.get_simulation_types()),
                        os.listdir(export_directory)))
    data = {}
    for file in files:
        match = re.match(r"(.+)_(\d+)\.csv", file)
        assert match, "Filename invalid despite being filtered"
        sim = match.group(1) + "_" + match.group(2)
        data[sim] = pd.read_csv(os.path.join(export_directory, file))
    return data


# pylint: disable=invalid-name
def mg(fig):
    """Wrap figure in a markdown div."""
    return dcc.Graph(figure=fig)


def get_layout(data: Dict[str, pd.DataFrame]) -> html:
    """Get the layout for the server."""
    tabs = []
    for sim, simdata in data.items():
        tabs.append(dcc.Tab(label=sim, children=[
            mg(graphs.get_table(simdata)),
            mg(graphs.get_line_plot(simdata)),
        ]))
    return html.Div([
        html.H1("Finance Simulation"),
        dcc.Tabs(tabs)
    ])
