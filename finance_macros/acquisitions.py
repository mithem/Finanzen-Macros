# coding: utf-8
"""Acquisition budgeting."""
import calendar
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Type, Callable, Any, Tuple, Union

from dateutil.relativedelta import relativedelta

ROW_START_IDX = 6
COLUMN_START_IDX = 0
# {column_name: (attribute_name, data_type, column_index)}
COLUMNS = {"Name": ("name", str, 0), "Startdatum": ("start_date", Optional[date], 1),
           "Zieldatum": ("target_date", Optional[date], 2),
           "Startbudget": ("start_budget", float, 3), "Zielbudget": ("target_budget", float, 4),
           "Davon allokiert": ("budget_acquired", float, 5), "Entsprechend verfügbar": None,
           "Anteil": None, "Gewichtung": ("weight", int, 8), "Debug": (None, str, 9), }
LIBRE_OFFICE_DATE_FORMAT = "%d.%m.%y"

try:
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Anschaffungen")

    PLANNING_MODE_CELL = sheet.getCellByPosition(12, 7)
    TODAY_OVERWRITE_CELL = sheet.getCellByPosition(6, 3)
    MONTHLY_BUDGET_CELL = sheet.getCellByPosition(12, 11)
    START_BUDGET_CELL = sheet.getCellByPosition(13, 3)
    ALREADY_ALLOCATED_WITHOUT_PLANNING_START_BUDGET_CELL = sheet.getCellByPosition(12, 5)
    PLANNING_DAY_OF_MONTH_CELL = sheet.getCellByPosition(12, 16)
except NameError:
    pass  # running tests


def _get_day_of_month_of_planning_date(planning_month: date, planning_day_of_month: int) -> int:
    """Return the day of month of the given planning date."""
    day_count = calendar.monthrange(planning_month.year, planning_month.month)[1]
    if planning_day_of_month > 0:
        return min(planning_day_of_month, day_count)
    return int(planning_day_of_month) if planning_day_of_month > 0 \
        else day_count + planning_day_of_month + 1


def _get_next_planning_date(current_date: date, planning_day_of_month: int) -> date:
    """Return the next planning date after the given current date."""
    this_months_planning = date(year=current_date.year, month=current_date.month,
                                day=_get_day_of_month_of_planning_date(current_date,
                                                                       planning_day_of_month))
    if this_months_planning > current_date:
        return this_months_planning
    approximately_next_planning = current_date + relativedelta(months=1)
    return date(year=approximately_next_planning.year, month=approximately_next_planning.month,
                day=_get_day_of_month_of_planning_date(approximately_next_planning,
                                                       planning_day_of_month))


def _planning_date_count_between(date1: date, date2: date, planning_day_of_month: int) -> int:
    """Return the number of planning dates between the two given dates."""
    counter = 1 if date1.day == _get_day_of_month_of_planning_date(date1,
                                                                   planning_day_of_month) else 0
    planning_date = _get_next_planning_date(date1, planning_day_of_month)
    while planning_date <= date2:
        counter += 1
        planning_date = _get_next_planning_date(planning_date, planning_day_of_month)
    return counter


class BaseAcquisition:
    """A base class for all acquisitions."""

    name: str
    start_budget: float
    target_budget: float
    budget_acquired: float
    start_date: Optional[date]
    target_date: Optional[date]
    weight: int

    # pylint: disable=too-many-arguments
    def __init__(self, name: str, start_budget: float, target_budget: float,
                 start_date: Optional[date],
                 target_date: Optional[date],
                 weight: int, ):
        self.name = name
        self.start_budget = start_budget
        self.target_budget = target_budget
        self.budget_acquired = self.start_budget
        self.start_date = start_date
        self.target_date = target_date
        self.weight = weight

    def request_budget(
            self,
            planning_date: Optional[date] = None
    ):
        """Return the amount of budget that is still needed to reach the target budget."""
        if self.weight == 0:
            return 0
        if self.start_date and planning_date and self.start_date > planning_date:
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
target_date={self.target_date}, \
target_budget={self.target_budget}, \
weight={self.weight})"

    def __repr__(self):
        return str(self)

    def planning_dates_until_target_date(self, planning_day_of_month: int) -> Optional[int]:
        """Return the number of planning dates until the target date."""
        if not self.start_date or not self.target_date:
            return None
        return _planning_date_count_between(
            self.start_date,
            self.target_date,
            planning_day_of_month
        )

    def start_date_sorting_key(self) -> Union[date, int]:
        """Return key used for sorting acquisitions by start date."""
        return self.start_date if self.start_date else 0


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
    planning_day_of_month: int

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            acquisitions: List[BaseAcquisition],
            monthly_budget: float,
            start_budget: float,
            today: Optional[date] = None,
            planning_day_of_month: int = 1
    ):
        self.acquisitions = acquisitions
        self.monthly_budget = monthly_budget
        self.sum_of_weights = sum(acquisition.weight for acquisition in self.acquisitions)
        self.start_budget = start_budget
        self.today = today or date.today()
        self._planning_dates = []
        self.planning_day_of_month = planning_day_of_month

    def sum_of_relevant_weights_at_planning_date(self, planning_date: date):
        """Return the sum of weights of all acquisitions that are relevant
        for the given planning date."""
        return sum(acquisition.weight for acquisition in
                   filter(
                       lambda a: a.request_budget(planning_date),
                       self.acquisitions)
                   )

    def sum_of_relevant_weights(self, planning_date: date):
        """Return the sum of weights of all acquisitions that are relevant"""
        return sum(acquisition.weight for acquisition in
                   filter(lambda a: a.request_budget(planning_date), self.acquisitions))

    def calculate_acquired_budgets(self):
        """Calculate the acquired budgets for all acquisitions at the `today` date."""
        raise NotImplementedError

    def get_earliest_planning_date(self) -> Optional[date]:
        """Return the earliest relevant planning date for this planning."""
        earliest_start_date = min(acquisition.start_date for acquisition in  # type: ignore
                                  filter(lambda a: a.start_date is not None, self.acquisitions))
        if earliest_start_date is None:
            earliest_start_date = self.today
        if earliest_start_date.day == _get_day_of_month_of_planning_date(
                earliest_start_date,
                self.planning_day_of_month
        ) and earliest_start_date.month == earliest_start_date.month and \
                earliest_start_date.year == earliest_start_date.year:
            return earliest_start_date
        earliest_planning_day = _get_next_planning_date(earliest_start_date,
                                                        self.planning_day_of_month)
        if earliest_start_date == self.today:
            return None
        return earliest_planning_day

    def call_at_each_planning_date(self, callback: Callable[[
        date], Optional[float]]) -> float:
        """Call the given callback at each planning date until today.
        Return the sum of extra budget accumulated over the planning dates."""
        planning_date = self.get_earliest_planning_date()
        if not planning_date:  # either no planning date at all or just today
            return 0
        self._planning_dates = []
        value_sum: float = 0
        while planning_date <= self.today:
            self._planning_dates.append(planning_date)
            value = callback(planning_date)
            if value is not None:
                value_sum += value
            planning_date = _get_next_planning_date(planning_date, self.planning_day_of_month)
        return value_sum


class BasePlanningWeightedMonthlyContribution(BasePlanning):
    """Class for all plannings using the weighted monthly contribution mode."""

    def allocate_budget(self, budget: float, planning_date: date,
                        sum_of_weights_at_planning_date: int):
        """Allocate budget to all acquisitions that are relevant for the given planning date."""
        if budget == 0:
            return
        remaining_budget = budget
        for acquisition in self.acquisitions:
            if acquisition.start_date and acquisition.start_date > planning_date:
                continue
            requested_budget = acquisition.request_budget(planning_date)
            if requested_budget > 0:
                available_budget = max(
                    0.0,
                    budget * acquisition.weight / sum_of_weights_at_planning_date
                )
                budget_to_allocate = min(remaining_budget, available_budget, requested_budget)
                acquisition.allocate_budget(budget_to_allocate)
                remaining_budget -= budget_to_allocate
        if 0 < remaining_budget < budget:
            # needs to be recalculated if extra_budget is available as some acquisition is fully
            # funded and therefore doesn't apply anymore
            self.allocate_budget(remaining_budget, planning_date,
                                 self.sum_of_relevant_weights_at_planning_date(planning_date))

    def allocate_planning_start_budget(self, budget: float):
        """Allocate the planning's start budget to all acquisitions, depending on their weight."""
        # planning_date = self.get_earliest_planning_date()
        # return self.allocate_budget(budget, planning_date,
        # self.sum_of_relevant_weights_at_planning_date(planning_date))
        extra_budget = 0
        sum_of_weights = self.sum_of_relevant_weights(self.today)
        for acquisition in self.acquisitions:
            requested_budget = acquisition.request_budget(self.today)
            if requested_budget == 0:
                continue
            if sum_of_weights == 0:  # all acquisitions allocated for 100%
                return
            available_budget = max(budget * acquisition.weight / sum_of_weights, 0)
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
        available_budget = max(self.start_budget, 0)
        acq_count = len(acquisition_sequence)
        acq_idx = 0
        while available_budget and acq_idx < acq_count:
            requested_budget = acquisition_sequence[acq_idx].request_budget(self.today)
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
        available_budget = max(budget, 0)
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
            acq_idx = self.allocate_budget(
                self.monthly_budget,
                acquisition_sequence,
                acq_idx
            )
            planning_date = _get_next_planning_date(planning_date, self.planning_day_of_month)


class BasePlanningDatedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    """Planning using the sequential acquisition mode with a priority
    sequence of `start_date`, `weight`, `target_budget`, `name`."""

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        budget_sorted = sorted(name_sorted, key=lambda a: a.target_budget)
        weight_sorted = sorted(budget_sorted, key=lambda a: a.weight, reverse=True)
        return sorted(weight_sorted, key=lambda a: a.start_date_sorting_key())


class BasePlanningWeightedSequentialAcquisition(BasePlanningBaseSequentialAcquisition):
    """Planning using the sequential acquisition mode with a priority
    sequence of `weight`, `target_budget`, `start_date`, `name`."""

    def get_acquisition_sequence(self) -> List[BaseAcquisition]:
        # sort by weight, then budget, then date, then name
        name_sorted = sorted(self.acquisitions, key=lambda a: a.name)
        date_sorted = sorted(name_sorted, key=lambda a: a.start_date_sorting_key())
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
        date_sorted = sorted(name_sorted, key=lambda a: a.start_date_sorting_key())
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
        available = max(budget / len(relevant_acquisitions), 0)
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


class BasePlanningTargetDate(BasePlanning):
    """Planning mode that allocates budgets in a way
    that the target budget is reached at the target date. Acquisitions
    without a target date are allocated immediately (prioritized). Acquisitions
    with higher weights are prioritized (with or without target budget)."""

    def immediate_allocation_required(
            self,
            acquisitions: List[BaseAcquisition],
            planning_date: date
    ) -> Tuple[float, List[BaseAcquisition]]:
        """Return the amount of budget that acquisitions require which have no
        end date scheduled."""
        acqs = list(filter(lambda a: a.target_date is None or a.start_date is None, acquisitions))
        return sum(map(lambda a: a.request_budget(planning_date), acqs)), acqs

    def allocate_budget(self, budget: float, planning_date: date) -> float:
        """Allocate a one-time budget (e.g. of a month or a starting budget).
        The remaining (extra, more than could be allocated) budget is returned."""
        remaining_budget = budget
        acquisitions = sorted(self.acquisitions, key=lambda a: a.weight, reverse=True)
        immediate_allocation_budget, immediate_acquisitions = self. \
            immediate_allocation_required(acquisitions, planning_date)

        # Allocate budget to acquisitions without a target date
        planning = BasePlanningWeightedMonthlyContribution(immediate_acquisitions, 0, 0, self.today)
        budget_to_allocate = max(0.0, min(remaining_budget, immediate_allocation_budget))
        planning.allocate_budget(budget_to_allocate, self.today,
                                 planning.sum_of_relevant_weights_at_planning_date(self.today))
        remaining_budget -= budget_to_allocate

        for acq in acquisitions:
            requested = acq.request_budget(planning_date)
            num_planning_dates = acq.planning_dates_until_target_date(self.planning_day_of_month)
            if num_planning_dates is None or num_planning_dates == 0:
                num_planning_dates = 1
            if acq.start_date:
                allocation_deficit = \
                    (acq.target_budget - acq.start_budget) / num_planning_dates \
                    * _planning_date_count_between(
                        acq.start_date, planning_date, self.planning_day_of_month
                    ) - acq.budget_acquired + acq.start_budget
            else:
                allocation_deficit = requested
            to_allocate = max(
                0.0,
                min(
                    allocation_deficit,
                    requested,
                    remaining_budget
                )
            )
            if to_allocate > 0:
                acq.allocate_budget(to_allocate)
                remaining_budget -= to_allocate
        return remaining_budget

    def calculate_acquired_budgets(self):
        earliest_planning_date = self.get_earliest_planning_date()
        extra_budget = self.allocate_budget(
            self.start_budget, earliest_planning_date if earliest_planning_date else self.today
        )
        value = self.call_at_each_planning_date(
            lambda planning_date: self.allocate_budget(self.monthly_budget, planning_date)
        )
        if value is not None:
            extra_budget += value
        if extra_budget:
            self.allocate_budget(extra_budget, self.today)


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
        if expected_type in (str, date, Optional[date]):
            value = cell.getString()
        else:
            value = cell.getValue()
        if expected_type == int:
            return int(value)
        if expected_type == float:
            return float(value)
        if expected_type == date:
            return datetime.strptime(value, LIBRE_OFFICE_DATE_FORMAT).date()
        if expected_type == Optional[date]:
            return datetime.strptime(value, LIBRE_OFFICE_DATE_FORMAT).date() if value else None
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
        monthly_budget = MONTHLY_BUDGET_CELL.getValue()
        self.planning_debug_cell = sheet.getCellByPosition(0, 4)
        value = TODAY_OVERWRITE_CELL.getString()
        today: Optional[date] = None
        if value:
            today = datetime.strptime(value, LIBRE_OFFICE_DATE_FORMAT).date()
        if start_budget is None:
            start_budget = START_BUDGET_CELL.getValue()
        day_of_month = int(PLANNING_DAY_OF_MONTH_CELL.getValue())
        super().__init__(acquisitions, monthly_budget, start_budget, today=today,
                         planning_day_of_month=day_of_month)

    @staticmethod
    def get_acquisitions():
        """Return the acquisitions read from the spreadsheet."""
        acquisitions: List[SpreadsheetAcquisition] = []
        end = 100
        for row in range(ROW_START_IDX, end):
            name = sheet.getCellByPosition(COLUMN_START_IDX, row).getString()
            if name:
                acquisition = SpreadsheetAcquisition(row)
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
planning_dates={planning_dates}, \
start_budget={self.start_budget})"
        self.planning_debug_cell.setString(debug_info)

    def write_sum_of_acquired_budgets(self):
        """Write the sum of acquired budgets to the spreadsheet."""
        sum_of_acquired_budgets = sum(
            acquisition.budget_acquired for acquisition in self.acquisitions)
        ALREADY_ALLOCATED_WITHOUT_PLANNING_START_BUDGET_CELL.setValue(sum_of_acquired_budgets)


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


class SpreadsheetPlanningTargetDate(SpreadsheetPlanning, BasePlanningTargetDate):
    """Planning with target date mode."""


class PlanningMode(Enum):
    """Enum for the different planning modes."""

    WEIGHTED_MONTHLY_CONTRIBUTION = 1
    DATED_SEQUENTIAL_ACQUISITION = 2
    WEIGHTED_SEQUENTIAL_ACQUISITION = 3
    BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_ASCENDING = 4
    BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_DESCENDING = 5
    EGALITARIAN_DISTRIBUTION = 6
    TARGET_DATE = 7

    @staticmethod
    def read_from_spreadsheet():  # python 3.11, here we come (-> Self)!
        """Read the planning mode from the spreadsheet."""
        value = PLANNING_MODE_CELL.getString()
        mode: PlanningMode
        if value == "Gewichtete monatliche Allokation":
            mode = PlanningMode.WEIGHTED_MONTHLY_CONTRIBUTION
        elif value == "Datierte sequenzielle Allokation":
            mode = PlanningMode.DATED_SEQUENTIAL_ACQUISITION
        elif value == "Gewichtete sequenzielle Allokation":
            mode = PlanningMode.WEIGHTED_SEQUENTIAL_ACQUISITION
        elif value == "Budgetorientierte sequenzielle Allokation (aufsteigend)":
            mode = PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_ASCENDING
        elif value == "Budgetorientierte sequenzielle Allokation (absteigend)":
            mode = PlanningMode.BUDGET_ORIENTED_SEQUENTIAL_ACQUISITION_DESCENDING
        elif value == "Egalitäre Verteilung":
            mode = PlanningMode.EGALITARIAN_DISTRIBUTION
        elif value == "Zieldatum":
            mode = PlanningMode.TARGET_DATE
        else:
            raise ValueError(f"Unsupported planning mode '{value}'")
        return mode


def _calculate_budgets_of_type(
        PlanningType: Type[SpreadsheetPlanning], ):  # pylint: disable=invalid-name
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
        PlanningMode.EGALITARIAN_DISTRIBUTION: SpreadsheetPlanningEgalitarianDistribution,
        PlanningMode.TARGET_DATE: SpreadsheetPlanningTargetDate,
    }
    for mode_type, planning in mode_map.items():
        if mode == mode_type:
            _calculate_budgets_of_type(planning)
            return
    raise ValueError(f"Invalid PlanningMode '{mode}'")


g_exportedScripts = (calculate_budgets,)
