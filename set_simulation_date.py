# coding: utf-8
from __future__ import unicode_literals
import datetime

desktop = XSCRIPTCONTEXT.getDesktop()
model = desktop.getCurrentComponent()
sheet = model.getSheets().getByName("Anschaffungen")

SIMULATION_DATE_CELL = sheet.getCellByPosition(6, 3)
LIBRE_OFFICE_DATE_FORMAT = "%d.%m.%y"


def _set_to_date_in_months(months: int):
    def _get_potential_day(day: int):
        try:
            return datetime.date(months_later.year, months_later.month, day)
        except ValueError:
            return _get_potential_day(day - 1)

    today = datetime.datetime.now().date()
    months_later = today + datetime.timedelta(days=months * 30)
    months_later = _get_potential_day(today.day)
    string = months_later.strftime(LIBRE_OFFICE_DATE_FORMAT)
    SIMULATION_DATE_CELL.setString(string)


def SetDateToToday(*args):
    _set_to_date_in_months(0)


def SetDateToInThreeMonths(*args):
    _set_to_date_in_months(3)


def SetDateToInSixMonths(*args):
    _set_to_date_in_months(6)


def SetDateToInAYear(*args):
    _set_to_date_in_months(12)


g_exportedScript = (
    SetDateToToday,
    SetDateToInThreeMonths,
    SetDateToInSixMonths,
    SetDateToInAYear,
)
