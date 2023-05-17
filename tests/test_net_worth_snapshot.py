import datetime

import finance_macros.net_worth_snapshot as nws


def test_get_date_value():
    date = datetime.date(year=2023, month=5, day=17)
    assert nws._date_value(date) == 45063


def test_get_date_value_2():
    date = datetime.date(year=1900, month=1, day=1)
    assert nws._date_value(date) == 2
