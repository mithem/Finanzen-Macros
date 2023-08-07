import os
import re

import pandas as pd
from dash import Dash, dcc, html

from finance_macros.simulation import graphs
from finance_macros.simulation.config import Config

CONFIG = Config()

app = Dash(__name__)
app.title = "Finance Simulation"


def run(export_directory: str):
    """Run the server."""
    app.layout = get_layout(export_directory)
    app.run_server()


def load_data(export_directory: str) -> dict[str, pd.DataFrame]:
    files = list(filter(lambda f: any(f.startswith(sim_type.key + "_") for sim_type in
                                      CONFIG.get_simulation_types()),
                        os.listdir(export_directory)))
    data = {}
    for file in files:
        match = re.match(r"(.+)_(\d+)\.csv", file)
        sim = match.group(1) + "_" + match.group(2)
        data[sim] = pd.read_csv(os.path.join(export_directory, file))
    return data


def mg(fig):
    return dcc.Graph(figure=fig)


def get_layout(export_directory: str) -> html:
    data = load_data(export_directory)
    tabs = []
    for sim, df in data.items():
        tabs.append(dcc.Tab(label=sim, children=[
            mg(graphs.get_table(df)),
            mg(graphs.get_line_plot(df)),
        ]))

    return html.Div([
        html.H1("Finance Simulation"),
        dcc.Tabs(tabs)
    ])
