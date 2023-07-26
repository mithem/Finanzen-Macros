import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from finance_macros.data_visualization import FIXED_SCENARIO_RETURN, DATE_COLUMN


def get_fortune_history_line_plot(net_worth_history: pd.DataFrame, avg_return: float) -> go.Figure:
    """Get a line plot of the fortune history."""
    fig = go.Figure(layout=go.Layout(title="Fortune History"))
    delta_depot_value = net_worth_history["Depotwert"].diff()
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Depotwert"],
                   name="Depotwert"))
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=delta_depot_value, name="Depotschwankung"))
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Avg scenario"],
                   name=f"Avg Scenario ({round(avg_return * 100, 2)}%)"))
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Fixed scenario"],
                   name=f"Fixed Scenario ({round(FIXED_SCENARIO_RETURN * 100, 2)}%)"))
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Net Worth"],
                   name="Net Worth"))
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Davon nicht Depot"],
                   name="Davon nicht Depot"))
    return fig


def get_fortune_history_area_plot(net_worth_history: pd.DataFrame) -> go.Figure:
    fig = px.area(net_worth_history, x=DATE_COLUMN, y=["Depotwert", "Davon nicht Depot"],
                  title="Depotwert")
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Net Worth"],
                   name="Net Worth",
                   line=go.scatter.Line(color="limegreen", dash="dash")))
    return fig


def get_current_net_worth_composition_pie(net_worth_history: pd.DataFrame) -> go.Figure:
    labels = ["Depotwert", "Davon nicht Depot"]
    display_values = [net_worth_history["Depotwert"].iloc[-1],
                      net_worth_history["Davon nicht Depot"].iloc[-1]]
    fig = go.Figure(
        data=[go.Pie(labels=labels, values=display_values, textinfo="label+percent+value")],
        layout_title_text="Net Worth Composition")
    return fig


def get_depot_value_fluctuation_histogram(net_worth_history: pd.DataFrame) -> go.Figure:
    delta_depot_value = net_worth_history["Depotwert"].diff()
    delta_depot_value = delta_depot_value[1:]
    stddev = delta_depot_value.std()
    median = delta_depot_value.median()
    mean = delta_depot_value.mean()

    def calculate_share_of_values_being_within_stddev(k) -> float:
        return len(
            [i for i in delta_depot_value if
             median - k * stddev <= i <= median + k * stddev]) / len(
            delta_depot_value)

    depot_value_fluctuations = sorted(delta_depot_value)
    fig = px.histogram(depot_value_fluctuations, marginal="box", nbins=10)
    colors = ["red", "purple", "green", "orange"]
    fig.add_vline(x=median, line_width=3, line_dash="dash", line_color=colors[0])
    fig.add_vline(x=mean, line_width=3, line_dash="dash", line_color=colors[1], annotation={
        "text": f"Mean: {round(mean, 2)}",
    })
    for k in range(1, 3):
        fig.add_vline(x=median + k * stddev, line_width=3, line_dash="dash",
                      line_color=colors[k + 1])
        fig.add_annotation(x=median + k * stddev,
                           text=f"{round(calculate_share_of_values_being_within_stddev(k) * 100, 2)}%",
                           showarrow=False)
        fig.add_vline(x=median - k * stddev, line_width=3, line_dash="dash",
                      line_color=colors[k + 1])
        fig.add_annotation(x=median - k * stddev,
                           text=f"{round(calculate_share_of_values_being_within_stddev(k) * 100, 2)}%",
                           showarrow=False)
    return fig


def get_net_worth_bubble_chart(net_worth_history: pd.DataFrame) -> go.Figure:
    sizes = net_worth_history["Depotwert"]
    sizes_normalized = (sizes - sizes.min()) / (sizes.max() - sizes.min())
    bubble_chart = go.Scatter(
        x=net_worth_history[DATE_COLUMN],
        y=net_worth_history["Net Worth"],
        mode='markers',
        marker=dict(
            size=sizes_normalized,
            sizemode='diameter',
            sizeref=sizes_normalized.max() / 30,
            sizemin=3,
            color=net_worth_history["Depotwert"],
            colorscale='Viridis',
            showscale=True
        ),
    )
    fig = go.Figure(data=[bubble_chart])
    fig.update_layout(
        title='Net Worth',
        xaxis_title='Datum',
        yaxis_title='Net Worth',
    )
    return fig


def get_depot_composition_by_shares_pie(composition_history: pd.DataFrame) -> go.Figure:
    labels = composition_history.keys()[1:]
    values = composition_history.iloc[-1][1:]
    return go.Figure(data=[go.Pie(labels=labels, values=values, textinfo="label+percent+value")],
                     layout_title_text="Depot Composition (shares)")


def get_depot_composition_by_value_pie(value_history: pd.DataFrame) -> go.Figure:
    labels = value_history.keys()[1:]
    values = value_history.iloc[-1][1:]
    return go.Figure(data=[go.Pie(labels=labels, values=values, textinfo="label+percent+value")],
                     layout_title_text="Depot Composition (value)")


def get_quotes_history_line_plot(quote_history: pd.DataFrame) -> go.Figure:
    labels = quote_history.keys()[1:]
    return px.line(quote_history, x=DATE_COLUMN, y=labels, title="Quotes")


def get_depot_composition_history_line_plot(composition_history: pd.DataFrame) -> go.Figure:
    labels = composition_history.keys()[1:]
    return px.line(composition_history, x=DATE_COLUMN, y=labels, title="Stock Counts")


def get_depot_value_history_line_plot(value_history: pd.DataFrame) -> go.Figure:
    labels = value_history.keys()[1:]
    return px.line(value_history, x=DATE_COLUMN, y=labels, title="Stock Values")


def get_depot_value_history_area_plot(value_history: pd.DataFrame) -> go.Figure:
    labels = value_history.keys()[1:]
    return px.area(value_history, x=DATE_COLUMN, y=labels, title="Stock Values")


def get_avg_performance_gauge(avg_return: float) -> go.Figure:
    value = avg_return * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": "Avg Performance"},
        gauge={
            "bar": {"color": "darkblue"},
            "steps": [
                {
                    "range": [3, 5],
                    "color": "orange"
                },
                {
                    "range": [5, 7],
                    "color": "yellow"
                },
                {
                    "range": [7, 10],
                    "color": "limegreen"
                },
                {
                    "range": [10, 15],
                    "color": "cyan"
                },
                {
                    "range": [15, 20],
                    "color": "purple"
                }
            ],
        },
        number={
            "suffix": "%"
        }
    ))
    return fig


def get_net_worth_gauge(net_worth_history: pd.DataFrame):
    value = net_worth_history["Net Worth"].iloc[-1]
    reference = net_worth_history["Net Worth"].iloc[-7]
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": "Net Worth"},
        gauge={
            "bar": {"color": "darkblue"},
        },
        delta={
            "reference": reference,
        },
        number={
            "prefix": "€"
        }
    ))
    return fig


def get_depot_value_gauge(net_worth_history: pd.DataFrame):
    value = net_worth_history["Depotwert"].iloc[-1]
    reference = net_worth_history["Depotwert"].iloc[-7]
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": "Depotwert"},
        gauge={
            "bar": {"color": "darkblue"},
        },
        delta={
            "reference": reference,
        },
        number={
            "prefix": "€"
        }
    ))
    return fig


def get_stock_quote_line(quote_history: pd.DataFrame) -> go.Figure:
    return px.line(quote_history, x=DATE_COLUMN, y=quote_history.keys()[1:], title="Quotes")
