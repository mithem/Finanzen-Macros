import argparse

from dash import Dash, html, dcc
from dash.dcc import Graph

from finance_macros.data_visualization import get_net_worth_history, get_depot_history
from finance_macros.data_visualization import graphs

parser = argparse.ArgumentParser()
parser.add_argument("export_directory",
                    help="The directory where the exports are stored.")
args = parser.parse_args()

net_worth_history, avg_return = get_net_worth_history(args.export_directory)
composition_history, quote_history, value_history = get_depot_history(args.export_directory)

app = Dash(__name__)


def mg(fig, style: dict = None):
    if style is None:
        style = {}
    return Graph(figure=fig, style=style)


def fortune_history_line():
    return mg(graphs.get_fortune_history_line_plot(net_worth_history, avg_return))


def fortune_history_area():
    return mg(graphs.get_fortune_history_area_plot(net_worth_history))


def net_worth_composition_pie():
    return mg(graphs.get_current_net_worth_composition_pie(net_worth_history),
              style={"width": "33%"})


def depot_value_fluctuation_histogram():
    return mg(graphs.get_depot_value_fluctuation_histogram(net_worth_history))


def depot_composition_by_value():
    return mg(graphs.get_depot_composition_by_value_pie(value_history),
              style={"width": "33%"})


def depot_composition_by_shares():
    return mg(graphs.get_depot_composition_by_shares_pie(composition_history),
              style={"width": "33%"})


def net_worth_bubble():
    return mg(graphs.get_net_worth_bubble_chart(net_worth_history))


def depot_value_history_area():
    return mg(graphs.get_depot_value_history_area_plot(value_history))


def depot_value_history_line():
    return mg(graphs.get_depot_value_history_line_plot(value_history))


def avg_performance_gauge():
    return mg(graphs.get_avg_performance_gauge(avg_return), style={"width": "33%"})


def net_worth_gauge():
    return mg(graphs.get_net_worth_gauge(net_worth_history), style={"width": "33%"})


def depot_value_gauge():
    return mg(graphs.get_depot_value_gauge(net_worth_history), style={"width": "33%"})


app.layout = html.Div([
    html.H1("Net Worth Dashboard"),
    html.Div([
        avg_performance_gauge(),
        net_worth_gauge(),
        depot_value_gauge()
    ], style={"display": "flex", "flex-direction": "row"}),
    html.Div([
        net_worth_composition_pie(),
        depot_composition_by_value(),
        depot_composition_by_shares()
    ], style={"display": "flex", "flex-direction": "row"}),
    fortune_history_area(),
    fortune_history_line(),
    dcc.Tabs([
        dcc.Tab(label="Net Worth Bubble", children=[
            html.Div([
                net_worth_bubble()
            ])
        ]),
        dcc.Tab(label="Depot Value Fluctuation Histogram", children=[
            html.Div([
                depot_value_fluctuation_histogram()
            ])
        ]),
        dcc.Tab(label="Depot value composition", children=[
            html.Div([
                depot_value_history_area(),
                depot_value_history_line()
            ])
        ])
    ])
], style={"font-family": "'Open Sans', verdana, arial, sans-serif"})

if __name__ == "__main__":
    app.run_server(debug=True)
