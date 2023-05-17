# coding: utf-8
"""Acquisition budgeting."""
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, List, Optional, Type, Callable

ROW_START_IDX = 6
COLUMN_START_IDX = 0
# {column_name: (attribute_name, data_type, column_index)}
COLUMNS = {"Name": ("name", str, 0), "Startdatum": ("start_date", date, 1),
           "Startbudget": ("start_budget", float, 2), "Zielbudget": ("target_budget", float, 3),
           "Davon allokiert": ("budget_acquired", float, 4), "Entsprechend verfügbar": None,
           "Anteil": None, "Gewichtung": ("weight", int, 7), "Debug": (None, str, 8), }
PLANNING_DAY_OF_MONTH = 1
LIBRE_OFFICE_DATE_FORMAT = "%d.%m.%y"

try:
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Anschaffungen")
except NameError:
    pass  # running tests


class BaseAcquisition:
    """A base class for all acquisitions."""

    name: str
    start_budget: float
    target_budget: float
    budget_acquired: float
    start_date: date
    weight: int

    # pylint: disable=too-many-arguments
    def __init__(self, name: str, start_budget: float, target_budget: float, start_date: date,
                 weight: int, ):
        self.name = name
        self.start_budget = start_budget
        self.target_budget = target_budget
        self.budget_acquired = self.start_budget
        self.start_date = start_date
        self.weight = weight

    def request_budget(self):
        """Return the amount of budget that is still needed to reach the target budget."""
        if self.weight == 0:
            return 0
        return self.target_budget - self.budget_acquired

    def allocate_budget(self, budget: float):
        """Allocate budget to this acquisition."""
        self.budget_acquired += budget

    def __str__(self):
        return f"{self.name}(\
budget_acquired={self.budget_acquired}, \
start_date={self.start_date}, \
start_budget={self.start_budget}, \
target_budget={self.target_budget}, \
weight={self.weight})"

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

    def __init__(self, acquisitions: List[BaseAcquisition], monthly_budget: float,
                 start_budget: float, today: Optional[date] = None, ):
        self.acquisitions = acquisitions
        self.monthly_budget = monthly_budget
        self.sum_of_weights = sum(acquisition.weight for acquisition in self.acquisitions)
        self.start_budget = start_budget
        self.today = today or date.today()
        self._planning_dates = []

    def sum_of_relevant_weights_at_planning_date(self, planning_date: date):
        """Return the sum of weights of all acquisitions that are relevant
        for the given planning date."""
        return sum(acquisition.weight for acquisition in
                   filter(lambda a: a.start_date <= planning_date and a.request_budget(),
                          self.acquisitions, ))

    def sum_of_relevant_weights(self):
        """Return the sum of weights of all acquisitions that are relevant"""
        return sum(acquisition.weight for acquisition in
                   filter(lambda a: a.request_budget(), self.acquisitions))

    def calculate_acquired_budgets(self):
        """Calculate the acquired budgets for all acquisitions at the `today` date."""
        raise NotImplementedError

    def get_earliest_planning_date(self) -> Optional[date]:
        """Return the earliest relevant planning date for this planning."""
        earliest_start_date = min(acquisition.start_date for acquisition in self.acquisitions)
        earliest_planning_day = date(earliest_start_date.year, earliest_start_date.month,
                                     PLANNING_DAY_OF_MONTH)
        if earliest_start_date == self.today:
            return None
        if earliest_planning_day < earliest_start_date:
            tmp = earliest_planning_day + timedelta(days=32)
            earliest_planning_day = date(year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH)
        return earliest_planning_day

    def call_at_each_planning_date(self, callback: Callable[[date], None]):
        """Call the given callback at each planning date until today."""
        planning_date = self.get_earliest_planning_date()
        if not planning_date:  # either no planning date at all or just today
            return
        self._planning_dates = []
        while planning_date <= self.today:
            self._planning_dates.append(planning_date)
            callback(planning_date)
            planning_date = self.get_next_planning_date(planning_date)

    def get_next_planning_date(self, planning_date: date) -> date:
        """Return the next planning date after the given planning date."""
        tmp = planning_date + timedelta(days=32)
        return date(year=tmp.year, month=tmp.month, day=PLANNING_DAY_OF_MONTH)


class BasePlanningWeightedMonthlyContribution(BasePlanning):
    """Class for all plannings using the weighted monthly contribution mode."""

    def allocate_budget(self, budget: float, planning_date: date,
                        sum_of_weights_at_planning_date: int):
        """Allocate budget to all acquisitions that are relevant for the given planning date."""
        if budget == 0:
            return
        extra_budget = 0
        for acquisition in self.acquisitions:
            if acquisition.start_date > planning_date:
                continue
            requested_budget = acquisition.request_budget()
            if requested_budget > 0:
                available_budget = budget * acquisition.weight / sum_of_weights_at_planning_date
                budget_to_allocate = min(available_budget, requested_budget)
                acquisition.allocate_budget(budget_to_allocate)
                extra_budget += available_budget - budget_to_allocate
        if extra_budget:
            # needs to be recalculated if extra_budget is available as some acquisition is fully
            # funded and therefore doesn't apply anymore
            self.allocate_budget(extra_budget, planning_date,
                                 self.sum_of_relevant_weights_at_planning_date(planning_date))

    def allocate_planning_start_budget(self, budget: float):
        """Allocate the planning's start budget to all acquisitions, depending on their weight."""
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
        def monthly_allocation(planning_date: date):
            self.allocate_budget(self.monthly_budget, planning_date,
                                 self.sum_of_relevant_weights_at_planning_date(planning_date))

        if not self.acquisitions:
            return
        self.allocate_planning_start_budget(self.start_budget)
        self.call_at_each_planning_date(monthly_allocation)


class BasePlanningBaseSequentialAcquisition(BasePlanning):
    """Class for all plannings using the sequential acquisition mode (using different sequences)."""

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        """Return the sequence acquisitions should be acquired in."""
        raise NotImplementedError

    def allocate_planning_start_budget(self, acquisition_sequence: List[BaseAcquisition]):
        """Allocate the planning's start budget to all acquisitions in the given sequence."""
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

    def allocate_budget(self, budget: float, acquisition_sequence: List[BaseAcquisition],
                        acq_idx: int) -> int:
        """Allocate budget to all acquisitions in the
        given sequence (if available) starting at the given index.
        Return index for currently allocating acquisition.
        """
        if budget == 0:
            return acq_idx
        acq_count = len(acquisition_sequence)
        available_budget = budget
        while acq_idx < acq_count and available_budget:
            requested_budget = acquisition_sequence[acq_idx].request_budget()
            if requested_budget > available_budget:
                acquisition_sequence[acq_idx].allocate_budget(available_budget)
                available_budget = 0
            else:
                acquisition_sequence[acq_idx].allocate_budget(requested_budget)
                available_budget -= requested_budget
                acq_idx += 1
        return acq_idx

    def calculate_acquired_budgets(self):
        acquisition_sequence = self.get_acquisition_sequence()
        acq_idx = 0
        acq_count = len(acquisition_sequence)
        planning_date = self.get_earliest_planning_date()
        if not planning_date:  # either no planning date at all or just today
            return
        self.allocate_planning_start_budget(acquisition_sequence)
        while planning_date <= self.today and acq_idx < acq_count:
            acq_idx = self.allocate_budget(self.monthly_budget, acquisition_sequence, acq_idx)
            planning_date = self.get_next_planning_date(planning_date)


class BasePlanningDatedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    """Planning using the sequential acquisition mode with a priority
    sequence of `start_date`, `weight`, `target_budget`, `name`."""

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        budget_sorted = sorted(name_sorted, key=lambda a: a.target_budget)
        weight_sorted = sorted(budget_sorted, key=lambda a: a.weight, reverse=True)
        return sorted(weight_sorted, key=lambda a: a.start_date)


class BasePlanningWeightedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    """Planning using the sequential acquisition mode with a priority
    sequence of `weight`, `target_budget`, `start_date`, `name`."""

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        # sort by weight, then budget, then date, then name
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        date_sorted = sorted(name_sorted, key=lambda a: a.start_date)
        budget_sorted = sorted(date_sorted, key=lambda a: a.target_budget)
        return sorted(budget_sorted, key=lambda a: a.weight, reverse=True)


class BasePlanningBudgetOrientedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    """Planning using the sequential acquisition mode with a priority
    sequence of `target_budget`, `weight`, `start_date`, `name`."""

    # Whether to allocate by target budgets in ascending or descending order.
    ascending: bool

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        # sort by budget, then weight, then date, then name
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        date_sorted = sorted(name_sorted, key=lambda a: a.start_date)
        weight_sorted = sorted(date_sorted, key=lambda a: a.weight, reverse=True)
        return sorted(weight_sorted, key=lambda a: a.target_budget, reverse=not self.ascending)


class BasePlanningEgalitarianDistribution(BasePlanning):
    """Planning mode that distributes the budget equally among all acquisitions, regardless of
    start_date, budget, weight, etc."""

    def allocate_budget(self, budget: float):
        """Allocate budget to all acquisitions in the planning equally."""
        relevant_acquisitions = list(filter(lambda a: a.request_budget(), self.acquisitions))
        if not relevant_acquisitions:
            return
        available = budget / len(relevant_acquisitions)
        extra_budget = 0
        for acq in relevant_acquisitions:
            requested = acq.request_budget()
            if requested >= available:
                acq.allocate_budget(available)
            else:
                acq.allocate_budget(requested)
                extra_budget += available - requested
        if extra_budget and sum(map(lambda a: a.request_budget(), self.acquisitions)):
            self.allocate_budget(extra_budget)

    def calculate_acquired_budgets(self):
        def monthly_allocation(_):
            self.allocate_budget(self.monthly_budget)

        self.allocate_budget(self.start_budget)
        self.call_at_each_planning_date(monthly_allocation)


class SpreadsheetAcquisition(BaseAcquisition):
    """Class for acquisitions read from the spreadsheet."""

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
        """Extract the value from the given cell, converting it to the
        `expected_type` if necessary."""
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
        """Write the relevant values of this acquisition to the spreadsheet."""

        budget_acquired_cell = sheet.getCellByPosition(
            COLUMNS["Davon allokiert"][2],  # type: ignore
            self.row
        )
        budget_acquired_cell.setValue(self.budget_acquired)

    def clear_debug_info(self):
        """Clear the debug info of this acquisition from the spreadsheet."""
        sheet.getCellByPosition(COLUMNS["Debug"][2], self.row).setString(  # type: ignore
            "")

    def write_debug_info(self):
        """Write the debug info of this acquisition to the spreadsheet."""
        sheet.getCellByPosition(COLUMNS["Debug"][2], self.row).setString(  # type: ignore
            str(self))


class SpreadsheetPlanning(BasePlanning):  # pylint: disable=abstract-method
    """Class for reading the planning data from the spreadsheet."""

    planning_debug_cell: Any
    acquisitions: List[SpreadsheetAcquisition]  # type: ignore

    def __init__(self, start_budget: Optional[float] = None):
        acquisitions = SpreadsheetPlanning.get_acquisitions()
        monthly_budget = sheet.getCellByPosition(10, 11).getValue()
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
        """Return the acquisitions read from the spreadsheet."""
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
        """Write the relevant values of this planning to the spreadsheet."""
        for acquisition in self.acquisitions:
            acquisition.write_values()

    def clear_debug_info(self):
        """Clear the debug info of this planning from the spreadsheet."""
        for acquisition in self.acquisitions:
            acquisition.clear_debug_info()

        self.planning_debug_cell.setString("")

    def write_debug_info(self):
        """Write the debug info of this planning to the spreadsheet."""
        for acquisition in self.acquisitions:
            acquisition.write_debug_info()

        planning_dates = (
                "[" + ", ".join(map(lambda d: str(d),  # pylint: disable=unnecessary-lambda
                                    self._planning_dates, )) + "]")
        debug_info = f"Planning(monthly_budget={self.monthly_budget}, \
sum_of_weights={self.sum_of_weights}, \
months={len(self._planning_dates)}, \
planning_dates={planning_dates})"
        self.planning_debug_cell.setString(debug_info)

    def write_sum_of_acquired_budgets(self):
        """Write the sum of acquired budgets to the spreadsheet."""
        sum_of_acquired_budgets = sum(
            acquisition.budget_acquired for acquisition in self.acquisitions)
        sheet.getCellByPosition(10, 5).setValue(sum_of_acquired_budgets)


class SpreadsheetPlanningWeightedMonthlyContribution(SpreadsheetPlanning,
                                                     BasePlanningWeightedMonthlyContribution):
    """Planning with weighted monthly contribution mode."""


class SpreadsheetPlanningDatedSequentialAcquisition(SpreadsheetPlanning,
                                                    BasePlanningDatedSequentialAcquisition):
    """Planning with dated sequential acquisition mode."""


class SpreadsheetPlanningWeightedSequentialAcquisition(SpreadsheetPlanning,
                                                       BasePlanningWeightedSequentialAcquisition):
    """Planning with weighted sequential acquisition mode."""


class SpreadsheetPlanningBudgetOrientedSequentialAcquisitionAscending(
    SpreadsheetPlanning,
    BasePlanningBudgetOrientedSequentialAcquisition
):
    """Planning with budget oriented sequential acquisition mode (ascending)."""

    def __init__(self, start_budget: Optional[float] = None):
        super().__init__(start_budget)
        self.ascending = True


class SpreadsheetPlanningBudgetOrientedSequentialAcquisitionDescending(
    SpreadsheetPlanning,
    BasePlanningBudgetOrientedSequentialAcquisition
):
    """Planning with budget oriented sequential acquisition mode (descending)."""

    def __init__(self, start_budget: Optional[float] = None):
        super().__init__(start_budget)
        self.ascending = False


class SpreadsheetPlanningEgalitarianDistribution(SpreadsheetPlanning,
                                                 BasePlanningEgalitarianDistribution):
    """Planning with egalitarian distribution mode."""


class PlanningMode(Enum):
    """Enum for the different planning modes."""

    WEIGHTED_MONTHLY_CONTRIBUTION = 1
    DATED_SEQUENTIAL_ACQUISITION = 2
    WEIGHTED_SEQUENTIAL_ACQUISITION = 3
    BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_ASCENDING = 4
    BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_DESCENDING = 5
    EGALITARIAN_DISTRIBUTION = 6

    @staticmethod
    def read_from_spreadsheet():  # python 3.11, here we come (-> Self)!
        """Read the planning mode from the spreadsheet."""
        value = sheet.getCellByPosition(10, 7).getString()
        if value == "Gewichtete monatliche Allokation":
            return PlanningMode.WEIGHTED_MONTHLY_CONTRIBUTION
        if value == "Datierte sequenzielle Allokation":
            return PlanningMode.DATED_SEQUENTIAL_ACQUISITION
        if value == "Gewichtete sequenzielle Allokation":
            return PlanningMode.WEIGHTED_SEQUENTIAL_ACQUISITION
        if value == "Budgetorientierte sequenzielle Allokation (aufsteigend)":
            return PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_ASCENDING
        if value == "Budgetorientierte sequenzielle Allokation (absteigend)":
            return PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_DESCENDING
        if value == "Egalitäre Verteilung":
            return PlanningMode.EGALITARIAN_DISTRIBUTION
        raise ValueError(f"Unsupported planning mode '{value}'")


def _calculate_budgets_of_type(PlanningType: Type[SpreadsheetPlanning], ):  # pylint: disable=invalid-name
    """Calculate the acquired budgets for the given planning mode."""
    planning_without_start_budget = PlanningType(start_budget=0)
    planning_without_start_budget.calculate_acquired_budgets()
    planning_without_start_budget.write_sum_of_acquired_budgets()

    main_planning = PlanningType()
    main_planning.calculate_acquired_budgets()
    main_planning.write_values()


def calculate_budgets(*args):  # pylint: disable=invalid-name,unused-argument
    """Calculate the acquired budgets for the planning mode on the spreadsheet."""
    mode = PlanningMode.read_from_spreadsheet()
    mode_map = {
        PlanningMode.WEIGHTED_MONTHLY_CONTRIBUTION: SpreadsheetPlanningWeightedMonthlyContribution,
        PlanningMode.DATED_SEQUENTIAL_ACQUISITION: SpreadsheetPlanningDatedSequentialAcquisition,
        PlanningMode.WEIGHTED_SEQUENTIAL_ACQUISITION:
            SpreadsheetPlanningWeightedSequentialAcquisition,
        PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_ASCENDING:
            SpreadsheetPlanningBudgetOrientedSequentialAcquisitionAscending,
        PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_DESCENDING:
            SpreadsheetPlanningBudgetOrientedSequentialAcquisitionDescending,
        PlanningMode.EGALITARIAN_DISTRIBUTION: SpreadsheetPlanningEgalitarianDistribution}
    for mode_type, planning in mode_map.items():
        if mode == mode_type:
            _calculate_budgets_of_type(planning)
            return
    raise ValueError(f"Invalid PlanningMode '{mode}'")


g_exportedScripts = (calculate_budgets,)
