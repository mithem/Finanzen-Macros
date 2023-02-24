from datetime import date
from acquisitions import BaseAcquisition, BasePlanning


def test_acquisition():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    assert acquisition.request_budget() == 100
    acquisition.allocate_budget(50)
    assert acquisition.request_budget() == 50
    assert acquisition.budget_acquired == 50


def test_planning_allocate_budget_single_acquisition():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 1, 15)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=10, today=today)
    planning.allocate_budget(planning.monthly_budget, date(2023, 1, 1), 1)
    assert acquisition.budget_acquired == 10


def test_planning_calculate_acquired_budgets_doesnt_start_on_today():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 1, 1)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=10, today=today)
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 0


def test_planning_calculate_acquired_budgets_does_start_on_first_day_in_past():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 1, 2)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=10, today=today)
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 10


def test_planning_calculate_acquired_budgets_single_acquisition_before_start():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 12, 15)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=10, today=today)
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 0


def test_planning_calculate_acquired_budgets_single_acquisition_interim():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=10, today=today)
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 30


def test_planning_calculate_acquired_budgets_single_acquisition_after_end():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 6, 15)
    planning = BasePlanning(acquisitions=[acquisition], monthly_budget=20, today=today)
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 100


def test_planning_calculate_acquired_budgets_two_acquisitions_before_start():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 12, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2], monthly_budget=10, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 0
    assert acquisition2.budget_acquired == 0


def test_planning_calculate_acquired_budgets_two_acquisitions_interim():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2], monthly_budget=10, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 17.5
    assert acquisition2.budget_acquired == 22.5


def test_planning_calculate_acquired_budgets_two_acquisitions_after_end_uses_extra_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=500,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 7, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2], monthly_budget=40, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 100
    assert acquisition2.budget_acquired == 220


def test_planning_calculate_acquired_budgets_three_acquisitions_interim_uses_extra_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 90 + 2.5
    assert acquisition2.budget_acquired == 50
    assert acquisition3.budget_acquired == 90 + 7.5


def test_planning_calculate_acquired_budgets_three_acquisitions_interim():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 4, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 100
    assert acquisition2.budget_acquired == 50
    march = 97.5
    april = 60 - 7.5
    assert acquisition3.budget_acquired == march + april  # 150


def test_planning_calculate_acquired_budgets_three_acquisitions_after_end():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        budget_acquired=0,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        budget_acquired=0,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 7, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 100
    assert acquisition2.budget_acquired == 50
    assert acquisition3.budget_acquired == 150 + 60 * 3
