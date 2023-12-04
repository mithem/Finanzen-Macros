"""Snapshot function for net worth history table."""
import datetime
import os

DATE_COLUMN = 4
NET_WORTH_COLUMN = 5
DEPOT_VALUE_COLUMN = 6
NOT_IN_DEPOT_COLUMN = 7
FIRST_DATA_ROW = 63

try:
    # pylint: disable=undefined-variable
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Sparen")
    EXPORT_DIRECTORY = sheet.getCellByPosition(8, 11).getString()
    NET_WORTH_CELL = sheet.getCellByPosition(NET_WORTH_COLUMN, 45)
    DEPOT_VALUE_CELL = sheet.getCellByPosition(NET_WORTH_COLUMN, 46)
except NameError:  # running tests
    EXPORT_DIRECTORY = "~/"


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
    current_net_worth = NET_WORTH_CELL.getValue()
    current_depot_value = DEPOT_VALUE_CELL.getValue()

    sheet.getCellByPosition(DATE_COLUMN, row).setValue(_date_value(today))
    sheet.getCellByPosition(NET_WORTH_COLUMN, row).setValue(current_net_worth)
    sheet.getCellByPosition(DEPOT_VALUE_COLUMN, row).setValue(current_depot_value)


def write_csv(*args):  # pylint: disable=unused-argument
    """Write the net worth history table to a csv file."""
    with open(os.path.join(EXPORT_DIRECTORY, "net_worth_history.csv"), "w",
              encoding="utf-8") as file:
        row = FIRST_DATA_ROW
        columns = {"Net Worth": NET_WORTH_COLUMN, "Depotwert": DEPOT_VALUE_COLUMN,
                   "Davon nicht Depot": NOT_IN_DEPOT_COLUMN}
        date = _get_date_value(row)
        file.write("Datum")
        for col in columns:
            file.write(";" + col)
        file.write("\n")
        while date:
            file.write(date)
            for col_nr in columns.values():
                file.write(";" + str(sheet.getCellByPosition(col_nr, row).getValue()))
            file.write("\n")
            row += 1
            date = _get_date_value(row)
