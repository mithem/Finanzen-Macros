# coding: utf-8
from __future__ import unicode_literals

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, List, Optional, Type

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
    "Anteil": None,
    "Gewichtung": ("weight", int, 7),
    "Debug": (None, str, 8),
}
PLANNING_DAY_OF_MONTH = 1
LIBRE_OFFICE_DATE_FORMAT = "%d.%m.%y"

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
        start_date: date,
        weight: int,
    ):
        self.name = name
        self.start_budget = start_budget
        self.target_budget = target_budget
        self.budget_acquired = self.start_budget
        self.start_date = start_date
        self.weight = weight

    def request_budget(self):
        return self.target_budget - self.budget_acquired

    def allocate_budget(self, budget: float):
        self.budget_acquired += budget

    def __str__(self):
        return f"{self.name}(budget_acquired={self.budget_acquired}, tart_date={self.start_date}, start_budget={self.start_budget}, target_budget={self.target_budget}, weight={self.weight})"

    def __repr__(self):
        return str(self)


class BasePlanning:
    """A base class for all plannings, regardless of their mode."""

    acquisitions: List[BaseAcquisition]
    monthly_budget: float
    sum_of_weights: int
    # to allocate to all acquisitions as a starting budget depending on their weight
    # regardless of their start date.
    # Useful for example when irregular income boosts capital.
    # Reads extra cell on spreadsheet currently depending on account surplus.
    start_budget: float
    today: date  # for testing
    _planning_dates: List[date]

    def __init__(
        self,
        acquisitions: List[BaseAcquisition],
        monthly_budget: float,
        start_budget: float,
        today: date = None,
    ):
        self.acquisitions = acquisitions
        self.monthly_budget = monthly_budget
        self.sum_of_weights = sum(
            [acquisition.weight for acquisition in self.acquisitions]
        )
        self.start_budget = start_budget
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

    def sum_of_relevant_weights(self):
        return sum(
            acquisition.weight
            for acquisition in filter(lambda a: a.request_budget(), self.acquisitions)
        )

    def calculate_acquired_budgets(self):
        raise NotImplementedError

    def get_earliest_planning_date(self) -> Optional[date]:
        earliest_start_date = min(
            [acquisition.start_date for acquisition in self.acquisitions]
        )
        earliest_planning_day = date(
            earliest_start_date.year, earliest_start_date.month, PLANNING_DAY_OF_MONTH
        )
        if earliest_start_date == self.today:
            return None
        if earliest_planning_day < earliest_start_date:
            tmp = earliest_planning_day + timedelta(days=32)
            earliest_planning_day = date(
                year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH
            )
        return earliest_planning_day

    @staticmethod
    def get_next_planning_date(planning_date: date) -> date:
        tmp = planning_date + timedelta(days=32)
        return date(year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH)


class BasePlanningWeightedMonthlyContribution(BasePlanning):
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

    def allocate_planning_start_budget(self, budget: float):
        extra_budget = 0
        sum_of_weights = self.sum_of_relevant_weights()
        for acquisition in self.acquisitions:
            requested_budget = acquisition.request_budget()
            if requested_budget == 0:
                continue
            if sum_of_weights == 0:  # all acquisitions allocated for 100%
                return
            available_budget = budget * acquisition.weight / sum_of_weights
            if requested_budget >= available_budget:
                acquisition.allocate_budget(available_budget)
            else:
                acquisition.allocate_budget(requested_budget)
                extra_budget += available_budget - requested_budget
        if extra_budget:
            self.allocate_planning_start_budget(extra_budget)

    def calculate_acquired_budgets(self):
        if not self.acquisitions:
            return
        self.allocate_planning_start_budget(self.start_budget)
        planning_date = self.get_earliest_planning_date()
        if not planning_date:  # either no planning date at all or just today
            return
        self._planning_dates = []
        while planning_date <= self.today:
            self._planning_dates.append(planning_date)
            sum_of_weights = self.sum_of_relevant_weights_at_planning_date(
                planning_date
            )
            self.allocate_budget(self.monthly_budget, planning_date, sum_of_weights)
            planning_date = BasePlanning.get_next_planning_date(planning_date)


class BasePlanningBaseSequentialAcquisition(BasePlanning):
    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        raise NotImplementedError

    def allocate_planning_start_budget(
        self, acquisition_sequence: List[BaseAcquisition]
    ):
        available_budget = self.start_budget
        acq_count = len(acquisition_sequence)
        acq_idx = 0
        while available_budget and acq_idx < acq_count:
            requested_budget = acquisition_sequence[acq_idx].request_budget()
            if requested_budget <= available_budget:
                acquisition_sequence[acq_idx].allocate_budget(requested_budget)
                available_budget -= requested_budget
            else:
                acquisition_sequence[acq_idx].allocate_budget(available_budget)
                return
            acq_idx += 1

    def calculate_acquired_budgets(self):
        acquisition_sequence = self.get_acquisition_sequence()
        acq_idx = 0
        acq_count = len(acquisition_sequence)
        planning_date = self.get_earliest_planning_date()
        if not planning_date:  # either no planning date at all or just today
            return
        self.allocate_planning_start_budget(acquisition_sequence)
        extra_budget = 0
        while planning_date <= self.today and acq_idx < acq_count:
            requested_budget = acquisition_sequence[acq_idx].request_budget()
            available_budget = self.monthly_budget + extra_budget
            if requested_budget <= available_budget:
                acquisition_sequence[acq_idx].allocate_budget(requested_budget)
                acq_idx += 1
                extra_budget += available_budget - requested_budget
            else:
                acquisition_sequence[acq_idx].allocate_budget(available_budget)
                extra_budget = 0
            planning_date = BasePlanning.get_next_planning_date(planning_date)


class BasePlanningDatedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        budget_sorted = sorted(name_sorted, key=lambda a: a.target_budget)
        weight_sorted = sorted(budget_sorted, key=lambda a: a.weight, reverse=True)
        return sorted(
            weight_sorted, key=lambda a: a.start_date
        )  # sort by start date, then by weight, then by target budget, then by name as sorted uses a stable sorting algorithm


class BasePlanningWeightedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        # sort by weight, then budget, then date, then name
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        date_sorted = sorted(name_sorted, key=lambda a: a.start_date)
        budget_sorted = sorted(date_sorted, key=lambda a: a.target_budget)
        return sorted(budget_sorted, key=lambda a: a.weight, reverse=True)


class SpreadsheetAcquisition(BaseAcquisition):
    row: int

    def __init__(self, row: int):
        properties = {}
        self.row = row
        for _, attribute in COLUMNS.items():
            if attribute and attribute[0]:
                cell = sheet.getCellByPosition(attribute[2], row)
                properties[attribute[0]] = self.extract_value(cell, attribute[1])
        # as that's only meant to be written, not read but instead
        # recalculated based on the other values
        del properties["budget_acquired"]
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
            return datetime.strptime(value, LIBRE_OFFICE_DATE_FORMAT).date()
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

    def __init__(self, start_budget: float = None):
        acquisitions = SpreadsheetPlanning.get_acquisitions()
        monthly_budget = (
            model.getSheets().getByName("Übersicht").getCellByPosition(1, 49).getValue()
        )
        self.planning_debug_cell = sheet.getCellByPosition(0, 4)
        today_overwrite_cell = sheet.getCellByPosition(6, 3)
        value = today_overwrite_cell.getString()
        today: Optional[date] = None
        if value:
            today = datetime.strptime(value, LIBRE_OFFICE_DATE_FORMAT).date()
        if start_budget is None:
            start_budget = sheet.getCellByPosition(11, 3).getValue()
        super().__init__(acquisitions, monthly_budget, start_budget, today=today)

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

    def write_sum_of_acquired_budgets(self):
        sum_of_acquired_budgets = sum(
            [acquisition.budget_acquired for acquisition in self.acquisitions]
        )
        sheet.getCellByPosition(10, 5).setValue(sum_of_acquired_budgets)


class SpreadsheetPlanningWeightedMonthlyContribution(
    SpreadsheetPlanning, BasePlanningWeightedMonthlyContribution
):
    pass


class SpreadsheetPlanningDatedSequentialAcquisition(
    SpreadsheetPlanning, BasePlanningDatedSequentialAcquisition
):
    pass


class SpreadsheetPlanningWeightedSequentialAcquisition(
    SpreadsheetPlanning, BasePlanningWeightedSequentialAcquisition
):
    pass


class PlanningMode(Enum):
    WEIGHTED_MONTHLY_CONTRIBUTION = 1
    DATED_SEQUENTIAL_ACQUISITION = 2
    WEIGHTED_SEQUENTIAL_ACQUISITION = 3

    @staticmethod
    def read_from_spreadsheet():  # python 3.11, here we come (-> Self)!
        value = sheet.getCellByPosition(10, 7).getString()
        if value == "Gewichtete monatliche Allokation":
            return PlanningMode.WEIGHTED_MONTHLY_CONTRIBUTION
        elif value == "Datierte sequenzielle Allokation":
            return PlanningMode.DATED_SEQUENTIAL_ACQUISITION
        elif value == "Gewichtete sequenzielle Allokation":
            return PlanningMode.WEIGHTED_SEQUENTIAL_ACQUISITION
        raise ValueError(f"Unsupported planning mode '{value}'")


def calculate_budgets(
    PlanningType: Type[SpreadsheetPlanning],
):  # pylint: disable=invalid-name
    planning_without_start_budget = PlanningType(start_budget=0)
    planning_without_start_budget.calculate_acquired_budgets()
    planning_without_start_budget.write_sum_of_acquired_budgets()

    main_planning = PlanningType()
    main_planning.calculate_acquired_budgets()
    main_planning.write_values()


def CalculateBudgets(*args):
    mode = PlanningMode.read_from_spreadsheet()
    if mode == PlanningMode.WEIGHTED_MONTHLY_CONTRIBUTION:
        calculate_budgets(SpreadsheetPlanningWeightedMonthlyContribution)
    elif mode == PlanningMode.DATED_SEQUENTIAL_ACQUISITION:
        calculate_budgets(SpreadsheetPlanningDatedSequentialAcquisition)
    elif mode == PlanningMode.WEIGHTED_SEQUENTIAL_ACQUISITION:
        calculate_budgets(SpreadsheetPlanningWeightedSequentialAcquisition)
    else:
        raise ValueError(f"Invalid PlanningMode '{mode}'")


g_exportedScripts = (CalculateBudgets,)
