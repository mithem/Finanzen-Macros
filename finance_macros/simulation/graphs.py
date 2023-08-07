"""Graphs for simulation module."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_table(data: pd.DataFrame) -> go.Figure:
    """Return a table with the given dataframe.
    :param data: dataframe to be displayed
    :return: plotly figure"""
    return go.Figure(data=[go.Table(
        header={
            "values": list(data.columns),
            "align": 'left'
        },
        cells={
            "values": [data[col] for col in data.columns],
            "align": 'left'
        })
    ])


def get_line_plot(data: pd.DataFrame) -> go.Figure:
    """Return a line plot with the given dataframe.
    :param data: dataframe to be displayed
    :return: plotly figure"""
    return px.line(data, x="date", y=data.columns[1:])
