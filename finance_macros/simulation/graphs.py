import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_table(df: pd.DataFrame) -> go.Figure:
    return go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    align='left'),
        cells=dict(values=[df[col] for col in df.columns],
                   align='left'))
    ])


def get_line_plot(df: pd.DataFrame) -> go.Figure:
    return px.line(df, x="date", y=df.columns[1:])
