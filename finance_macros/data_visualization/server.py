"""Dash server for the net worth dashboard."""
import argparse
import os
from typing import Optional

import darkdetect
from dash import Dash, html, dcc
from dash.dcc import Graph

from finance_macros.data_visualization import get_net_worth_history, get_depot_history
from finance_macros.data_visualization import graphs
from finance_macros.depot_composition import PortfolioComposition

parser = argparse.ArgumentParser()
parser.add_argument("--export-directory", "-e", required=True,
                    help="The directory where the exports are stored.")
parser.add_argument("--hostname", "-H", default="127.0.0.1")
args = parser.parse_args()

net_worth_history, net_worth_mvg_avg, avg_return = get_net_worth_history(args.export_directory)
composition_history, quote_history, value_history = get_depot_history(args.export_directory)
portfolio_composition = PortfolioComposition.load_from_csv(
    os.path.join(args.export_directory, "portfolio.csv"))

DARK_MODE = darkdetect.isDark()
BACKGROUND_COLOR = "black" if DARK_MODE else "#FFFFFF"
FONT_COLOR = "white" if DARK_MODE else "black"

app = Dash(__name__)
app.title = "Net Worth Dashboard"


def mg(fig, style: Optional[dict] = None):  # pylint: disable=invalid-name
    """Wrap a plotly figure in a dash Graph."""
    if style is None:
        style = {}
    fig.layout.template = "plotly_dark" if DARK_MODE else "plotly"
    return Graph(figure=fig, style=style)


def fortune_history_line():
    """Get a line plot of the fortune history."""
    return mg(graphs.get_fortune_history_line_plot(net_worth_history, avg_return))


def fortune_history_mvg_avg_line():
    """Get a line plot of the fortune history."""
    return mg(graphs.get_fortune_history_line_plot(net_worth_mvg_avg, avg_return))


def fortune_history_area():
    """Get an area plot of the fortune history."""
    return mg(graphs.get_fortune_history_area_plot(net_worth_history))


def net_worth_composition_pie():
    """Get a pie chart of the current net worth composition."""
    return mg(graphs.get_current_net_worth_composition_pie(net_worth_history),
              style={"width": "33%"})


def depot_value_fluctuation_histogram():
    """Get a histogram of the depot value fluctuations."""
    return mg(graphs.get_depot_value_fluctuation_histogram(net_worth_history))


def depot_composition_by_value():
    """Get a pie chart of the current depot composition by value."""
    return mg(graphs.get_depot_composition_by_value_pie(value_history),
              style={"width": "33%"})


def depot_composition_by_shares():
    """Get a pie chart of the current depot composition by shares."""
    return mg(graphs.get_depot_composition_by_shares_pie(composition_history),
              style={"width": "33%"})


def net_worth_bubble():
    """Get a bubble chart of the net worth history."""
    return mg(graphs.get_net_worth_bubble_chart(net_worth_history))


def depot_value_history_area():
    """Get an area plot of the depot value history."""
    return mg(graphs.get_depot_value_history_area_plot(value_history))


def depot_value_history_line():
    """Get a line plot of the depot value history."""
    return mg(graphs.get_depot_value_history_line_plot(value_history))


def depot_share_history_area():
    """Get an area plot of the depot share history."""
    return mg(graphs.get_depot_share_history_area_plot(composition_history))


def depot_share_history_line():
    """Get a line plot of the depot share history."""
    return mg(graphs.get_depot_share_history_line_plot(composition_history))


def avg_performance_gauge():
    """Get a gauge of the average performance."""
    return mg(graphs.get_avg_performance_gauge(avg_return), style={"width": "33%"})


def net_worth_gauge():
    """Get a gauge of the current net worth."""
    return mg(graphs.get_net_worth_gauge(net_worth_history, net_worth_mvg_avg),
              style={"width": "33%"})


def depot_value_gauge():
    """Get a gauge of the current depot value."""
    return mg(graphs.get_depot_value_gauge(net_worth_history, net_worth_mvg_avg),
              style={"width": "33%"})


def stock_quotes_line():
    """Get a line plot of the stock quotes."""
    return mg(graphs.get_stock_quote_line(quote_history))


def net_worth_position_type_sunburst():
    """Get a sunburst plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_position_type_sunburst(portfolio_composition))


def net_worth_position_type_treemap():
    """Get a treemap plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_position_type_treemap(portfolio_composition))


def net_worth_position_group_pie():
    """Get a pie plot of the net worth composition by position group."""
    return mg(graphs.get_net_worth_group_to_pos_type_sunburst(portfolio_composition))


def net_worth_position_summary_sunburst():
    """Get a sunburst plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_position_summary_sunburst(portfolio_composition))


def net_worth_position_summary_treemap():
    """Get a treemap plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_position_summary_treemap(portfolio_composition))


def net_worth_group_to_positions_sunburst():
    """Get a sunburst plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_group_to_positions_sunburst(portfolio_composition))


def net_worth_group_to_positions_treemap():
    """Get a treemap plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_group_to_positions_treemap(portfolio_composition))


def net_worth_group_to_pos_type_sunburst():
    """Get a sunburst plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_group_to_pos_type_sunburst(portfolio_composition))


def net_worth_group_to_pos_type_treemap():
    """Get a treemap plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_group_to_pos_type_treemap(portfolio_composition))


def net_worth_pos_type_to_group_sunburst():
    """Get a sunburst plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_pos_type_to_group_sunburst(portfolio_composition))


def net_worth_pos_type_to_group_treemap():
    """Get a treemap plot of the net worth composition by position type."""
    return mg(graphs.get_net_worth_pos_type_to_group_treemap(portfolio_composition))


css_flex_row = {"display": "flex", "flex-direction": "row"}
app.layout = html.Div([
    html.H1("Net Worth Dashboard"),
    html.Div([
        avg_performance_gauge(),
        net_worth_gauge(),
        depot_value_gauge()
    ], style=css_flex_row),
    dcc.Tabs([
        dcc.Tab(label="Overview", children=[
            html.Div([
                net_worth_position_type_sunburst(),
                net_worth_position_type_treemap()
            ], style=css_flex_row)
        ]),
        dcc.Tab(label="Position summary", children=[
            html.Div([
                net_worth_position_summary_sunburst(),
                net_worth_position_summary_treemap()
            ], style=css_flex_row)
        ]),
        dcc.Tab(label="Composition Overview", children=[
            html.Div([
                net_worth_composition_pie(),
                depot_composition_by_value(),
                depot_composition_by_shares()
            ], style=css_flex_row)
        ]),
        dcc.Tab(label="Positions by group", children=[
            html.Div([
                net_worth_group_to_positions_sunburst(),
                net_worth_group_to_positions_treemap()
            ], style=css_flex_row)
        ]),
        dcc.Tab(label="Position types by group", children=[
            html.Div([
                net_worth_group_to_pos_type_sunburst(),
                net_worth_group_to_pos_type_treemap()
            ], style=css_flex_row)
        ]),
        dcc.Tab(label="Position groups by type", children=[
            html.Div([
                net_worth_pos_type_to_group_sunburst(),
                net_worth_pos_type_to_group_treemap()
            ])
        ], style=css_flex_row)
    ]),
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
        ]),
        dcc.Tab(label="Depot share composition", children=[
            html.Div([
                depot_share_history_area(),
                depot_share_history_line()
            ])
        ]),
        dcc.Tab(label="Stock Quotes", children=[
            html.Div([
                stock_quotes_line()
            ])
        ]),
        dcc.Tab(label="Fortune mvg avg", children=[
            html.Div([
                fortune_history_mvg_avg_line()
            ])
        ])
    ])
], style={"font-family": "'Open Sans', verdana, arial, sans-serif",
          "background-color": BACKGROUND_COLOR, "color": FONT_COLOR})

if __name__ == "__main__":
    app.run_server(debug=True, host=args.hostname)
