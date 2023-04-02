# coding: utf-8
"""Set the planning simulation date in the spreadsheet."""
from __future__ import unicode_literals
import datetime

# pylint: disable=undefined-variable
desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
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


def SetDateToToday(*args):  # pylint: disable=invalid-name,unused-argument
    """Set the simulation date to today."""
    _set_to_date_in_months(0)


def SetDateToInThreeMonths(*args):  # pylint: disable=invalid-name,unused-argument
    """Set the simulation date to three months from now."""
    _set_to_date_in_months(3)


def SetDateToInSixMonths(*args):  # pylint: disable=invalid-name,unused-argument
    """Set the simulation date to six months from now."""
    _set_to_date_in_months(6)


def SetDateToInAYear(*args):  # pylint: disable=invalid-name,unused-argument
    """Set the simulation date to a year from now."""
    _set_to_date_in_months(12)


g_exportedScript = (
    SetDateToToday,
    SetDateToInThreeMonths,
    SetDateToInSixMonths,
    SetDateToInAYear,
)
