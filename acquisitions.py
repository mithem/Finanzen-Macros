# coding: utf-8
from __future__ import unicode_literals

from datetime import date, datetime, timedelta
from typing import Any, List

try:
    from com.sun.star.util import DateTime
except ImportError:
    pass  # running tests (not using Spreadsheet classes)


ROW_START_IDX = 6
COLUMN_START_IDX = 0
# {column_name: (attribute_name, data_type, column_index)}
COLUMNS = {
    "Name": ("name", str, 0),
    "Startdatum": ("start_date", date, 1),
    "Startbudget": ("start_budget", float, 2),
    "Zielbudget": ("target_budget", float, 3),
    "Davon allokiert": ("budget_acquired", float, 4),
    "Entsprechend verfügbar": None,
    "Gewichtung": ("weight", int, 6),
    "Debug": (None, str, 7),
}
PLANNING_DAY_OF_MONTH = 1

try:
    desktop = XSCRIPTCONTEXT.getDesktop()
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Anschaffungen")
except NameError:
    pass  # running tests


class BaseAcquisition:
    name: str
    start_budget: float
    target_budget: float
    budget_acquired: float
    start_date: date
    weight: int

    def __init__(
        self,
        name: str,
        start_budget: float,
        target_budget: float,
        budget_acquired: float,
        start_date: date,
        weight: int,
    ):
        self.name = name
        self.start_budget = start_budget
        self.target_budget = target_budget
        self.budget_acquired = budget_acquired
        self.start_date = start_date
        self.weight = weight

    def request_budget(self):
        return self.target_budget - self.budget_acquired

    def allocate_budget(self, budget):
        self.budget_acquired += budget

    def __str__(self):
        return f"{self.name}(budget_acquired={self.budget_acquired}, tart_date={self.start_date}, start_budget={self.start_budget}, target_budget={self.target_budget}, weight={self.weight})"

    def __repr__(self):
        return str(self)


class BasePlanning:
    acquisitions: List[BaseAcquisition]
    monthly_budget: float
    sum_of_weights: int
    today: date  # for testing
    _planning_dates: List[date]

    def __init__(
        self,
        acquisitions: List[BaseAcquisition],
        monthly_budget: float,
        today: date = None,
    ):
        self.acquisitions = acquisitions
        self.monthly_budget = monthly_budget
        self.sum_of_weights = sum(
            [acquisition.weight for acquisition in self.acquisitions]
        )
        self.today = today or date.today()
        self._planning_dates = []

    def sum_of_relevant_weights_at_planning_date(self, planning_date: date):
        return sum(
            acquisition.weight
            for acquisition in filter(
                lambda a: a.start_date <= planning_date and a.request_budget(),
                self.acquisitions,
            )
        )

    def allocate_budget(
        self, budget: float, planning_date: date, sum_of_weights_at_planning_date: int
    ):
        if budget == 0:
            return
        extra_budget = 0
        for acquisition in self.acquisitions:
            if acquisition.start_date > planning_date:
                continue
            requested_budget = acquisition.request_budget()
            if requested_budget > 0:
                available_budget = (
                    budget * acquisition.weight / sum_of_weights_at_planning_date
                )
                budget_to_allocate = min(available_budget, requested_budget)
                acquisition.allocate_budget(budget_to_allocate)
                extra_budget += available_budget - budget_to_allocate
        if extra_budget:
            self.allocate_budget(
                extra_budget,
                planning_date,
                self.sum_of_relevant_weights_at_planning_date(  # needs to be recalculated if extra_budget is available as some acquisition is fully funded and therefore doesn't apply anymore
                    planning_date
                ),
            )

    def calculate_acquired_budgets(self):
        if not self.acquisitions:
            return
        earliest_start_date = min(
            [acquisition.start_date for acquisition in self.acquisitions]
        )
        earliest_planning_day = date(
            earliest_start_date.year, earliest_start_date.month, PLANNING_DAY_OF_MONTH
        )
        if earliest_planning_day == self.today:
            return
        if earliest_planning_day < earliest_start_date:
            tmp = earliest_planning_day + timedelta(days=32)
            earliest_planning_day = date(
                year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH
            )
        planning_date = earliest_planning_day
        self._planning_dates = []
        while planning_date < self.today:
            self._planning_dates.append(planning_date)
            sum_of_weights = self.sum_of_relevant_weights_at_planning_date(
                planning_date
            )
            self.allocate_budget(self.monthly_budget, planning_date, sum_of_weights)
            tmp = planning_date + timedelta(days=32)
            planning_date = date(
                year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH
            )


class SpreadsheetAcquisition(BaseAcquisition):
    row: int

    def __init__(self, row: int):
        properties = {}
        self.row = row
        for _, attribute in COLUMNS.items():
            if attribute and attribute[0]:
                cell = sheet.getCellByPosition(attribute[2], row)
                properties[attribute[0]] = self.extract_value(cell, attribute[1])

        properties["budget_acquired"] = properties[
            "start_budget"
        ]  # so there's no state kept in the Spreadsheet, instead should be calculated every month since the start_date
        super().__init__(**properties)

    @staticmethod
    def extract_value(cell, expected_type):
        if expected_type in (str, date):
            value = cell.getString()
        else:
            value = cell.getValue()
        if expected_type == int:
            return int(value)
        if expected_type == float:
            return float(value)
        if expected_type == date:
            return datetime.strptime(value, "%d.%m.%y").date()
        return value

    def write_values(self):
        budget_acquired_cell = sheet.getCellByPosition(
            COLUMNS["Davon allokiert"][2], self.row
        )
        budget_acquired_cell.setValue(self.budget_acquired)

    def clear_debug_info(self):
        sheet.getCellByPosition(COLUMNS["Debug"][2], self.row).setString("")

    def write_debug_info(self):
        sheet.getCellByPosition(COLUMNS["Debug"][2], self.row).setString(str(self))


class SpreadsheetPlanning(BasePlanning):
    planning_debug_cell: Any

    def __init__(self):
        acquisitions = SpreadsheetPlanning.get_acquisitions()
        monthly_budget = (
            model.getSheets().getByName("Übersicht").getCellByPosition(1, 49).getValue()
        )
        self.planning_debug_cell = sheet.getCellByPosition(0, 4)
        super().__init__(acquisitions, monthly_budget)

    @staticmethod
    def get_acquisitions():
        acquisitions: List[SpreadsheetAcquisition] = []
        end = 100
        for row in range(ROW_START_IDX, end):
            name = sheet.getCellByPosition(COLUMN_START_IDX, row).getString()
            if name:
                acquisition = SpreadsheetAcquisition(row)
                if acquisition.start_date:
                    acquisitions.append(acquisition)
        return acquisitions

    def write_values(self):
        for acquisition in self.acquisitions:
            acquisition.write_values()

    def clear_debug_info(self):
        for acquisition in self.acquisitions:
            acquisition.clear_debug_info()

        self.planning_debug_cell.setString("")

    def write_debug_info(self):
        for acquisition in self.acquisitions:
            acquisition.write_debug_info()

        planning_dates = (
            "[" + ", ".join(map(lambda d: str(d), self._planning_dates)) + "]"
        )
        debug_info = f"Planning(monthly_budget={self.monthly_budget}, sum_of_weights={self.sum_of_weights}, months={len(self._planning_dates)}, planning_dates={planning_dates})"
        self.planning_debug_cell.setString(debug_info)


def CalculateBudgets(*args):
    planning = SpreadsheetPlanning()
    planning.calculate_acquired_budgets()
    planning.write_values()
    planning.clear_debug_info()

    # planning.write_debug_info()


g_exportedScripts = (CalculateBudgets,)
