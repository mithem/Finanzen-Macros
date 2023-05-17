"""Snapshot function for net worth history table."""
import datetime

DATE_COLUMN = 4
NET_WORTH_COLUMN = 5
DEPOT_VALUE_COLUMN = 6
FIRST_DATA_ROW = 55

try:
    # pylint: disable=undefined-variable
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Sparen")
except NameError:  # running tests
    pass


def _get_date_value(row: int) -> str:
    """Get the date value from the given row."""
    return sheet.getCellByPosition(DATE_COLUMN, row).getString()


def _date_value(date: datetime.date) -> int:
    delta = date - datetime.date(year=1900, month=1, day=1)
    return delta.days + 2


def snapshot_net_worth(*args):  # pylint: disable=invalid-name,unused-argument
    """Snapshot the current net worth and add it to the net worth history table."""
    row = FIRST_DATA_ROW
    date = _get_date_value(row)
    while date:
        row += 1
        date = _get_date_value(row)

    today = datetime.date.today()
    current_net_worth = sheet.getCellByPosition(NET_WORTH_COLUMN, 49).getValue()
    current_depot_value = sheet.getCellByPosition(5, 50).getValue()

    sheet.getCellByPosition(DATE_COLUMN, row).setValue(_date_value(today))
    sheet.getCellByPosition(NET_WORTH_COLUMN, row).setValue(current_net_worth)
    sheet.getCellByPosition(DEPOT_VALUE_COLUMN, row).setValue(current_depot_value)
