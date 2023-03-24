from datetime import date
from acquisitions import BaseAcquisition, BasePlanning


def _sum_acquired_budgets(*acquisitions: BaseAcquisition):
    return sum(acquisition.budget_acquired for acquisition in acquisitions)


def _sum_start_budgets(*acquisitions: BaseAcquisition):
    return sum(acquisition.start_budget for acquisition in acquisitions)


def assert_round(a: float, b: float):
    assert round(a, 2) == round(b, 2)


def test_acquisition():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
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
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 1, 15)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.allocate_budget(planning.monthly_budget, date(2023, 1, 1), 1)
    assert acquisition.budget_acquired == 10


def test_planning_calculate_acquired_budgets_doesnt_start_on_today():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 1, 1)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 0


def test_planning_calculate_acquired_budgets_does_start_on_first_day_in_past():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 1, 2)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 10


def test_planning_calculate_acquired_budgets_does_start_on_first_day_when_after_start_date():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 27),
        weight=1,
    )
    today = date(2023, 2, 1)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 10


def test_planning_calculate_acquired_budgets_single_acquisition_before_start():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 12, 15)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 0


def test_planning_calculate_acquired_budgets_single_acquisition_interim():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=10, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 30


def test_planning_calculate_acquired_budgets_single_acquisition_after_end():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 6, 15)
    planning = BasePlanning(
        acquisitions=[acquisition], monthly_budget=20, start_budget=0, today=today
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 100


def test_planning_calculate_acquired_budgets_two_acquisitions_before_start():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2022, 12, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=10,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 0
    assert acquisition2.budget_acquired == 0


def test_planning_calculate_acquired_budgets_two_acquisitions_interim():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=10,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 17.5
    assert acquisition2.budget_acquired == 22.5


def test_planning_calculate_acquired_budgets_two_acquisitions_after_end_uses_extra_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=500,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 7, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=40,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 100
    assert acquisition2.budget_acquired == 220


def test_planning_calculate_acquired_budgets_three_acquisitions_interim_uses_extra_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        start_budget=0,
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
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 4, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        start_budget=0,
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
        start_date=date(2022, 11, 15),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    acquisition3 = BaseAcquisition(
        name="test3",
        start_budget=0,
        target_budget=500,
        start_date=date(2023, 1, 1),
        weight=3,
    )
    today = date(2023, 7, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2, acquisition3],
        monthly_budget=60,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 100
    assert acquisition2.budget_acquired == 50
    assert acquisition3.budget_acquired == 150 + 60 * 3
    assert _sum_acquired_budgets(acquisition1, acquisition2, acquisition3) == 480


def test_planning_allocates_start_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2022, 9, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=10,
        start_budget=30,
        today=today,
    )
    planning.allocate_planning_start_budget(planning.start_budget)
    assert acquisition1.budget_acquired == 10
    assert acquisition2.budget_acquired == 20
    assert acquisition1.start_budget == 0
    assert acquisition2.start_budget == 0
    assert _sum_acquired_budgets(acquisition1, acquisition2) == planning.start_budget


def test_planning_allocates_start_budget_applies_extra_budget():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=100,
        start_date=date(2022, 9, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=10,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=10,
        start_budget=30,
        today=today,
    )
    planning.allocate_planning_start_budget(planning.start_budget)
    assert acquisition1.budget_acquired == 20
    assert acquisition2.budget_acquired == 10
    assert acquisition1.start_budget == 0
    assert acquisition2.start_budget == 0
    assert _sum_acquired_budgets(acquisition1, acquisition2) == planning.start_budget


def test_planning_allocate_start_budget_handles_satisfied_acquisitions():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=50,
        start_date=date(2022, 9, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=10,
        start_budget=150,
        today=today,
    )
    planning.allocate_planning_start_budget(planning.start_budget)
    assert acquisition1.budget_acquired == 50
    assert acquisition2.budget_acquired == 50
    assert acquisition1.start_budget == 0
    assert acquisition2.start_budget == 0
    assert _sum_acquired_budgets(acquisition1, acquisition2) == 100


def test_planning_allocate_start_budget_handles_satisfied_acquisitions_complex():
    ac1 = BaseAcquisition(
        name="test1",
        start_budget=0,
        target_budget=500,
        start_date=date(2022, 9, 1),
        weight=1,
    )
    ac2 = BaseAcquisition(
        name="test2",
        start_budget=0,
        target_budget=50,
        start_date=date(2023, 1, 1),
        weight=2,
    )
    ac3 = BaseAcquisition(
        name="test3",
        start_budget=10,
        target_budget=200,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[ac1, ac2, ac3],
        monthly_budget=10,
        start_budget=200,
        today=today,
    )
    planning.allocate_planning_start_budget(planning.start_budget)
    assert ac1.budget_acquired == 75
    assert ac2.budget_acquired == 50
    assert ac3.budget_acquired == 85
    assert ac1.start_budget == 0
    assert ac2.start_budget == 0
    assert ac3.start_budget == 10
    assert _sum_acquired_budgets(ac1, ac2, ac3) == planning.start_budget + 10


def test_planning_uses_start_budgets_before_first_planning_date():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=50,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 1, 1)
    planning = BasePlanning(
        acquisitions=[acquisition],
        monthly_budget=10,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 50
    assert acquisition.start_budget == 50


def test_planning_allocates_start_budget_long_term():
    acquisition = BaseAcquisition(
        name="test",
        start_budget=50,
        target_budget=100,
        start_date=date(2023, 1, 1),
        weight=1,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition],
        monthly_budget=10,
        start_budget=0,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition.budget_acquired == 80
    assert acquisition.start_budget == 50


def test_planning_end_to_end_simple():
    acquisition1 = BaseAcquisition(
        name="test1",
        start_budget=50,
        target_budget=200,
        start_date=date(2022, 12, 1),
        weight=1,
    )
    acquisition2 = BaseAcquisition(
        name="test2",
        start_budget=100,
        target_budget=500,
        start_date=date(2023, 1, 1),
        weight=4,
    )
    today = date(2023, 3, 15)
    planning = BasePlanning(
        acquisitions=[acquisition1, acquisition2],
        monthly_budget=50,
        start_budget=100,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert acquisition1.budget_acquired == 150
    assert acquisition2.budget_acquired == 300
    assert acquisition1.start_budget == 50
    assert acquisition2.start_budget == 100
    assert (
        _sum_acquired_budgets(acquisition1, acquisition2)
        == acquisition1.start_budget
        + acquisition2.start_budget
        + planning.start_budget
        + 50 * 4
    )


def test_end_to_end_complex():
    ac1 = BaseAcquisition(
        name="1",
        start_budget=0,
        target_budget=1500,
        start_date=date(2023, 2, 24),
        weight=2,
    )
    ac2 = BaseAcquisition(
        name="2",
        start_budget=50,
        target_budget=1000,
        start_date=date(2023, 2, 24),
        weight=1,
    )
    ac3 = BaseAcquisition(
        name="3",
        start_budget=0,
        target_budget=350,
        start_date=date(2023, 3, 10),
        weight=10,
    )
    ac4 = BaseAcquisition(
        name="4",
        start_budget=0,
        target_budget=1000,
        start_date=date(2023, 3, 19),
        weight=2,
    )
    ac5 = BaseAcquisition(
        name="5",
        start_budget=0,
        target_budget=800,
        start_date=date(2023, 3, 24),
        weight=1,
    )
    today = date(2023, 3, 24)
    acs = [ac1, ac2, ac3, ac4, ac5]
    planning = BasePlanning(
        acquisitions=acs,
        monthly_budget=328.64,
        start_budget=1000,
        today=today,
    )
    planning.calculate_acquired_budgets()
    assert_round(ac1.budget_acquired, 328.64 * 2 / 3 + 1000 * 2 / 16 + 275 * 2 / 6)
    assert_round(ac2.budget_acquired, 328.64 / 3 + 1000 / 16 + 275 / 6 + 50)
    assert_round(ac3.budget_acquired, 350)
    assert_round(ac4.budget_acquired, 1000 * 2 / 16 + 275 * 2 / 6)
    assert_round(ac5.budget_acquired, 1000 / 16 + 275 / 6)
    assert _sum_start_budgets(*acs) == 50
    assert _sum_acquired_budgets(*acs) == 1000 + 328.64 + 50
