"""Plotly graphs for the finance visualizations."""
import math
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from finance_macros.data_visualization import FIXED_SCENARIO_RETURN, DATE_COLUMN
from finance_macros.depot_composition import PortfolioComposition, PositionType, PositionGroup

INDICATOR_REFERENCE_DAY_INTERVAL = 7


def get_latest_values(data: pd.DataFrame) -> pd.DataFrame:
    """Get the latest values of the given dataframe."""
    keys = data.keys()[1:]
    index = -1
    while not all(not math.isnan(data[1:].iloc[index][key]) for key in keys):
        index -= 1
    return data[1:].iloc[index]


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
    """Get an area plot of the fortune history."""
    fig = px.area(net_worth_history, x=DATE_COLUMN, y=["Depotwert", "Davon nicht Depot"],
                  title="Depotwert")
    fig.add_trace(
        go.Scatter(x=net_worth_history[DATE_COLUMN], y=net_worth_history["Net Worth"],
                   name="Net Worth",
                   line=go.scatter.Line(color="limegreen", dash="dash")))
    return fig


def get_current_net_worth_composition_pie(net_worth_history: pd.DataFrame) -> go.Figure:
    """Get a pie chart of the current net worth composition."""
    labels = ["Depotwert", "Davon nicht Depot"]
    display_values = [net_worth_history["Depotwert"].iloc[-1],
                      net_worth_history["Davon nicht Depot"].iloc[-1]]
    fig = go.Figure(
        data=[go.Pie(labels=labels, values=display_values, textinfo="label+percent+value")],
        layout_title_text="Net Worth Composition")
    return fig


def get_depot_value_fluctuation_histogram(net_worth_history: pd.DataFrame) -> go.Figure:
    """Get a histogram of the depot value fluctuations."""
    delta_depot_value = net_worth_history["Depotwert"].diff()
    delta_depot_value = delta_depot_value[1:]
    stddev = delta_depot_value.std()
    median = delta_depot_value.median()
    mean = delta_depot_value.mean()

    def calculate_share_of_values_being_within_stddev(n) -> float:  # pylint: disable=invalid-name
        return len(
            [i for i in delta_depot_value if
             median - n * stddev <= i <= median + n * stddev]) / len(
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
                           text=str(round(calculate_share_of_values_being_within_stddev(k) * 100,
                                          2)) + "%",
                           showarrow=False)
        fig.add_vline(x=median - k * stddev, line_width=3, line_dash="dash",
                      line_color=colors[k + 1])
        fig.add_annotation(x=median - k * stddev,
                           text=str(round(calculate_share_of_values_being_within_stddev(k) * 100,
                                          2)) + "%",
                           showarrow=False)
    return fig


def get_net_worth_bubble_chart(net_worth_history: pd.DataFrame) -> go.Figure:
    """Get a bubble chart of the net worth history."""
    sizes = net_worth_history["Depotwert"]
    sizes_normalized = (sizes - sizes.min()) / (sizes.max() - sizes.min())
    bubble_chart = go.Scatter(
        x=net_worth_history[DATE_COLUMN],
        y=net_worth_history["Net Worth"],
        mode='markers',
        marker={
            "size": sizes_normalized,
            "sizemode": 'diameter',
            "sizeref": sizes_normalized.max() / 30,
            "sizemin": 3,
            "color": net_worth_history["Depotwert"],
            "colorscale": 'Viridis',
            "showscale": True
        },
    )
    fig = go.Figure(data=[bubble_chart])
    fig.update_layout(
        title='Net Worth',
        xaxis_title='Datum',
        yaxis_title='Net Worth',
    )
    return fig


def get_depot_composition_by_shares_pie(composition_history: pd.DataFrame) -> go.Figure:
    """Get a pie chart of the current depot composition by shares."""
    labels = composition_history.keys()[1:]
    values = get_latest_values(composition_history).values
    return go.Figure(data=[go.Pie(labels=labels, values=values, textinfo="label+percent+value")],
                     layout_title_text="Depot Composition (shares)")


def get_depot_composition_by_value_pie(value_history: pd.DataFrame) -> go.Figure:
    """Get a pie chart of the current depot composition by value."""
    labels = value_history.keys()[1:]
    values = get_latest_values(value_history).values
    return go.Figure(data=[go.Pie(labels=labels, values=values, textinfo="label+percent+value")],
                     layout_title_text="Depot Composition (value)")


def get_quotes_history_line_plot(quote_history: pd.DataFrame) -> go.Figure:
    """Get a line plot of the quotes history."""
    labels = quote_history.keys()[1:]
    return px.line(quote_history, x=DATE_COLUMN, y=labels, title="Quotes")


def get_depot_composition_history_line_plot(composition_history: pd.DataFrame) -> go.Figure:
    """Get a line plot of the depot composition history."""
    labels = composition_history.keys()[1:]
    return px.line(composition_history, x=DATE_COLUMN, y=labels, title="Stock Counts")


def get_depot_value_history_line_plot(value_history: pd.DataFrame) -> go.Figure:
    """Get a line plot of the depot value history."""
    labels = value_history.keys()[1:]
    return px.line(value_history, x=DATE_COLUMN, y=labels, title="Stock Values")


def get_depot_value_history_area_plot(value_history: pd.DataFrame) -> go.Figure:
    """Get an area plot of the depot value history."""
    labels = value_history.keys()[1:]
    return px.area(value_history, x=DATE_COLUMN, y=labels, title="Stock Values")


def get_depot_share_history_line_plot(share_history: pd.DataFrame) -> go.Figure:
    """Get a line plot of the depot share history."""
    labels = share_history.keys()[1:]
    return px.line(share_history, x=DATE_COLUMN, y=labels, title="Depot Share History")


def get_depot_share_history_area_plot(share_history: pd.DataFrame) -> go.Figure:
    """Get an area plot of the depot share history."""
    labels = share_history.keys()[1:]
    return px.area(share_history, x=DATE_COLUMN, y=labels, title="Depot Share History")


def get_avg_performance_gauge(avg_return: float) -> go.Figure:
    """Get a gauge of the average depot performance."""
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


def get_net_worth_gauge(net_worth_history: pd.DataFrame, mvg_avg: pd.DataFrame) -> go.Figure:
    """Get a gauge of the current net worth."""
    value = net_worth_history["Net Worth"].iloc[-1]
    reference = mvg_avg["Net Worth"].iloc[-INDICATOR_REFERENCE_DAY_INTERVAL]
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


def get_depot_value_gauge(net_worth_history: pd.DataFrame, mvg_avg: pd.DataFrame) -> go.Figure:
    """Get a gauge of the current depot value."""
    value = net_worth_history["Depotwert"].iloc[-1]
    reference = mvg_avg["Depotwert"].iloc[-INDICATOR_REFERENCE_DAY_INTERVAL]
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
    """Get a line plot of the stock quotes."""
    return px.line(quote_history, x=DATE_COLUMN, y=quote_history.keys()[1:], title="Quotes")


def _get_parent_name_from_type(type: PositionType) -> str:
    parent = PositionType.get_parent(type)
    return parent.value if parent else ""


def _get_name_from_group(group: PositionGroup) -> str:
    if group == PositionGroup.DEFAULT():
        return "Default"
    return group.display_value


def _get_net_worth_position_type_hierarchical_map(portfolio: PortfolioComposition) -> Dict[
    str, List[str | float]]:
    data = portfolio.get_position_type_value_composition()
    pos_types = data.keys()
    return {
        "labels": list(map(lambda type: type.value, pos_types)),
        "parents": list(map(_get_parent_name_from_type, pos_types)),
        "values": [data[type] for type in pos_types],
    }


def get_net_worth_position_type_sunburst(portfolio: PortfolioComposition) -> go.Figure:
    data = {
        **_get_net_worth_position_type_hierarchical_map(portfolio),
        "branchvalues": "total"
    }
    return go.Figure(go.Sunburst(**data, textinfo="label+percent entry+value"),
                     layout_title_text="Net worth composition by position type", layout_height=700)


def get_net_worth_position_type_treemap(portfolio: PortfolioComposition) -> go.Figure:
    data = _get_net_worth_position_type_hierarchical_map(portfolio)
    return go.Figure(go.Treemap(**data), layout_title_text="Net worth composition by position type")


def _get_net_worth_position_summary_hierarchical_map(portfolio: PortfolioComposition) -> Dict[
    str, List[str | float]]:
    labels = []
    parents = []
    values = []

    # individual positions
    for position in portfolio.positions:
        labels.append(position.name)
        parents.append(position.type.value)
        values.append(position.value)

    # position types
    data = portfolio.get_position_type_value_composition()
    pos_types = data.keys()
    for type in pos_types:
        labels.append(type.value)
        parents.append(_get_parent_name_from_type(type))
        values.append(data[type])

    data = {
        "labels": labels,
        "parents": parents,
        "values": values
    }
    return data


def _get_net_worth_group_to_positions_hierarchical_map(portfolio: PortfolioComposition) -> Dict[
    str, List[str | float]]:
    labels = []
    parents = []
    values = []

    # individual position
    for position in portfolio.positions:
        labels.append(position.name)
        parents.append(_get_name_from_group(position.group))
        values.append(position.value)

    # position groups
    data = portfolio.get_group_value_composition()
    net_worth = sum(values)
    groups = data.keys()
    all_groups_name = "All Groups"
    for group in groups:
        labels.append(_get_name_from_group(group))
        parents.append(all_groups_name)
        values.append(data[group])

    labels.append(all_groups_name)
    parents.append("")
    values.append(net_worth)

    data = {
        "labels": labels,
        "parents": parents,
        "values": values
    }
    return data


def _get_net_worth_group_to_pos_type_hierarchical_map(portfolio: PortfolioComposition) -> Dict[
    str, List[str | float]]:
    labels = []
    parents = []
    values = []
    group_data = portfolio.get_group_value_composition()
    all_groups_name = "All Groups"

    for group, value in group_data.items():
        group_name = _get_name_from_group(group)
        labels.append(group_name)
        parents.append(all_groups_name)
        values.append(value)
        for type in PositionType.get_all_types():
            sum_of_type_in_group = sum(position.value for position in
                                       filter(lambda pos: pos.type == type and pos.group == group, portfolio.positions))
            labels.append(type.name + "-" + group_name)
            parents.append(group_name)
            values.append(sum_of_type_in_group)

    labels.append(all_groups_name)
    parents.append("")
    values.append(sum(group_data.values()))

    data = {
        "labels": labels,
        "parents": parents,
        "values": values
    }
    return data


def _get_net_worth_pos_type_to_group_hierarchical_map(portfolio: PortfolioComposition) -> Dict[
    str, List[str | float]]:
    labels = []
    parents = []
    values = []
    group_data = portfolio.get_group_value_composition()

    for type in PositionType.get_all_types():
        labels.append(type.name)
        parents.append(PositionType.POSITION_TYPE.name)
        values.append(sum(position.value for position in
                          filter(lambda pos: pos.type == type, portfolio.positions)))
        for group, value in group_data.items():
            group_name = _get_name_from_group(group)
            labels.append(group_name + "-" + type.name)
            parents.append(type.name)
            values.append(sum(position.value for position in
                              filter(lambda pos: pos.type == type and pos.group == group, portfolio.positions)))

    labels.append(PositionType.POSITION_TYPE.name)
    parents.append("")
    values.append(sum(group_data.values()))

    data = {
        "labels": labels,
        "parents": parents,
        "values": values
    }
    return data


def get_net_worth_position_summary_sunburst(portfolio: PortfolioComposition) -> go.Figure:
    data = {
        **_get_net_worth_position_summary_hierarchical_map(portfolio),
        "branchvalues": "total"
    }
    return go.Figure(go.Sunburst(**data, textinfo="label+percent entry+value"),
                     layout_title_text="Position summary")


def get_net_worth_position_summary_treemap(portfolio: PortfolioComposition) -> go.Figure:
    data = _get_net_worth_position_summary_hierarchical_map(portfolio)
    return go.Figure(go.Treemap(**data), layout_title_text="Position summary")


def get_net_worth_group_to_positions_sunburst(portfolio: PortfolioComposition) -> go.Figure:
    data = {
        **_get_net_worth_group_to_positions_hierarchical_map(portfolio),
        "branchvalues": "total"
    }
    return go.Figure(go.Sunburst(**data, textinfo="label+percent entry+value"),
                     layout_title_text="Positions by position group")


def get_net_worth_group_to_positions_treemap(portfolio: PortfolioComposition) -> go.Figure:
    data = _get_net_worth_group_to_positions_hierarchical_map(portfolio)
    return go.Figure(go.Treemap(**data), layout_title_text="Positions by position group",
                     layout_height=700)


def get_net_worth_group_to_pos_type_sunburst(portfolio: PortfolioComposition) -> go.Figure:
    data = {
        **_get_net_worth_group_to_pos_type_hierarchical_map(portfolio),
        "branchvalues": "total"
    }
    return go.Figure(go.Sunburst(**data, textinfo="label+percent entry+value"),
                     layout_title_text="Position types by position group")


def get_net_worth_group_to_pos_type_treemap(portfolio: PortfolioComposition) -> go.Figure:
    data = _get_net_worth_group_to_pos_type_hierarchical_map(portfolio)
    return go.Figure(go.Treemap(**data), layout_title_text="Position types by position group",
                     layout_height=700)


def get_net_worth_pos_type_to_group_sunburst(portfolio: PortfolioComposition) -> go.Figure:
    data = {
        **_get_net_worth_pos_type_to_group_hierarchical_map(portfolio),
        "branchvalues": "total"
    }
    return go.Figure(go.Sunburst(**data, textinfo="label+percent entry+value"),
                     layout_title_text="Position groups by position type")


def get_net_worth_pos_type_to_group_treemap(portfolio: PortfolioComposition) -> go.Figure:
    data = _get_net_worth_pos_type_to_group_hierarchical_map(portfolio)
    return go.Figure(go.Treemap(**data), layout_title_text="Position groups by position type",
                     layout_height=700)
