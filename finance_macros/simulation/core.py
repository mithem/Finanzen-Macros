"""Core components for financial simulations"""
import datetime
import os
from typing import Callable, List, Dict, Optional

import pandas as pd


class Simulation:
    """Base class for financial simulations"""
    export_directory: str

    def __init__(self, export_directory: str):
        self.export_directory = export_directory

    def simulate(self):
        raise NotImplementedError

    def get_results(self) -> Dict:
        raise NotImplementedError

    def get_data(self) -> pd.DataFrame:
        return pd.DataFrame(self.get_results())

    def write_csv(self, filename: str):
        self.get_data().to_csv(os.path.join(self.export_directory, filename))


class TimeSeriesSimulation(Simulation):
    starting_date: datetime.date
    end_date: datetime.date
    _dates: List[datetime.date]

    def __init__(self, export_directory: str, starting_date: datetime.date,
                 end_date: datetime.date):
        super().__init__(export_directory)
        self.starting_date = starting_date
        self.end_date = end_date
        self._dates = [self.starting_date]

    def call_simulation_functions(self,
                                  daily_callback: Optional[Callable[[datetime.date], None]] = None,
                                  monthly_callback: Optional[
                                      Callable[[datetime.date], None]] = None,
                                  day_of_month: int = 1):
        date = self.starting_date
        while date <= self.end_date:
            date += datetime.timedelta(days=1)
            if daily_callback:
                daily_callback(date)
            if monthly_callback and date.day == day_of_month:
                monthly_callback(date)
            if daily_callback or (monthly_callback and date.day == day_of_month):
                self._dates.append(date)
