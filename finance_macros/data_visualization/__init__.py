import datetime
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd
from yahoofinancials import YahooFinancials

FIXED_SCENARIO_RETURN = .07
DATE_FORMAT = "%d.%m.%y"
DATE_COLUMN = "Datum"


def get_avg_return_scenario(data: pd.DataFrame, avg_return: float, data_key: str = "Depotwert") -> \
        List[float]:
    days_list = [(data[DATE_COLUMN].iloc[i] - data[DATE_COLUMN].iloc[0]).days for i in
                 range(len(data[DATE_COLUMN]))]
    return [data[data_key].iloc[0] * (1 + avg_return) ** (
        (i / 365)) for i in days_list]


def load_net_worth_history(filename: str) -> Tuple[pd.DataFrame, float]:
    """Load data from csv file and return it as a pandas dataframe"""
    df = pd.read_csv(filename, sep=";", decimal=".", parse_dates=[DATE_COLUMN],
                     date_format=DATE_FORMAT)
    avg_return = (df["Depotwert"].iloc[-1] / df["Depotwert"].iloc[0]) ** (
            365 / (df[DATE_COLUMN].iloc[-1] - df[DATE_COLUMN].iloc[0]).days) - 1
    df["Avg scenario"] = get_avg_return_scenario(df, avg_return)
    df["Fixed scenario"] = get_avg_return_scenario(df, FIXED_SCENARIO_RETURN)
    return df, avg_return


def load_depot_proposition_history(filename: str) -> pd.DataFrame:
    """Load data from csv file and return it as a pandas dataframe"""
    df = pd.read_csv(filename, sep=";", decimal=".", parse_dates=[DATE_COLUMN],
                     date_format=DATE_FORMAT)
    return df


def get_stock_quotes(depot_proposition_history: pd.DataFrame) -> pd.DataFrame:
    """Load stock quotes for the stocks in the depot proposition from yahoo."""
    positions = list(depot_proposition_history.keys()[1:])
    fin = YahooFinancials(positions, country="DE")
    sheet = fin.get_historical_price_data("2021-01-01", datetime.date.today().isoformat(), "daily")
    data = {}
    max_count = max([len(sheet[position]["prices"]) for position in positions])
    for position in positions:
        count = len(sheet[position]["prices"])
        data[position] = np.pad([sheet[position]["prices"][i]["close"] for i in
                                 range(len(sheet[position]["prices"]))], (max_count - count, 0),
                                constant_values=sheet[position]["prices"][0]["close"])
    df = pd.DataFrame()
    position = list(sheet.keys())[0]
    df[DATE_COLUMN] = [
        pd.Timestamp.fromisoformat(sheet[position]["prices"][i]["formatted_date"]) for i
        in
        range(len(sheet[position]["prices"]))]
    for position in positions:
        df[position] = data[position]
    return df


def interpolate_data_nonlinear(data: pd.DataFrame, start_date: Optional[pd.Timestamp] = None,
                               end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Interpolate data using a nonlinear interpolation method."""
    keys = data.keys()[1:]
    last_values = {}
    new_data = {DATE_COLUMN: []}
    date = start_date if start_date else data[DATE_COLUMN].iloc[0]
    end_date = end_date if end_date else data[DATE_COLUMN].iloc[-1]
    for key in keys:
        last_values[key] = data[key].iloc[0]
        new_data[key] = []
    while date < end_date:
        date_idx = data[DATE_COLUMN][data[DATE_COLUMN] == date].index
        if len(date_idx) > 0:
            for key in keys:
                value = data[key].iloc[date_idx[0]]
                last_values[key] = value
                new_data[key].append(value)
        else:
            for key in keys:
                new_data[key].append(last_values[key])
        new_data[DATE_COLUMN].append(date)
        date += datetime.timedelta(days=1)
    return pd.DataFrame(new_data)


def get_depot_history() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    proposition = load_depot_proposition_history("~/Desktop/depot_proposition.csv")
    quotes = get_stock_quotes(proposition)
    start_date = proposition[DATE_COLUMN].iloc[0]
    end_date = proposition[DATE_COLUMN].iloc[-1]
    proposition_history = interpolate_data_nonlinear(proposition)
    quotes_history = interpolate_data_nonlinear(quotes, start_date, end_date)
    values_history = pd.DataFrame()
    values_history[DATE_COLUMN] = proposition_history[DATE_COLUMN]
    for position in proposition.keys()[1:]:
        values_history[position] = proposition_history[position] * quotes_history[position]
    return proposition_history, quotes_history, values_history
