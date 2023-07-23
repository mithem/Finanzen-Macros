import datetime
import os

HEADER_ROW = 100
DATE_COLUMN = 9
PORTFOLIO_FIRST_ROW = 32
PORTFOLIO_IDENTIFIER_COLUMN = 3
PORTFOLIO_SHARE_COUNT_COLUMN = 8

try:
    # pylint: disable=undefined-variable
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Sparen")
    EXPORT_DIRECTORY = sheet.getCellByPosition(8, 11).getString()
except NameError:  # running tests
    EXPORT_DIRECTORY = "~/"


def snapshot_depot_proposition(*args):
    """Snapshot the current depot proposition and add it to the depot proposition history table."""
    positions = _get_positions()
    new_row = _get_new_row()
    _write_depot_proposition(positions, new_row)
    _write_current_date(new_row)


def _date_value(date: datetime.date) -> int:
    delta = date - datetime.date(year=1900, month=1, day=1)
    return delta.days + 2


def _write_current_date(row: int):
    sheet.getCellByPosition(DATE_COLUMN, row).setValue(_date_value(datetime.date.today()))


def _write_depot_proposition(positions, new_row: int):
    for i in range(len(positions)):
        sheet.getCellByPosition(DATE_COLUMN + i + 1, new_row).setValue(
            _get_share_count(positions[i]))


def _get_new_row():
    row = HEADER_ROW + 1
    date = sheet.getCellByPosition(DATE_COLUMN, row).getString()
    while date:
        row += 1
        date = sheet.getCellByPosition(DATE_COLUMN, row).getString()
    return row


def write_csv(*args):
    with open(os.path.join(EXPORT_DIRECTORY, "depot_proposition.csv"), "w") as f:
        positions = _get_positions()
        f.write("Datum")
        for position in positions:
            f.write(";" + position)
        f.write("\n")
        row = HEADER_ROW + 1
        date = sheet.getCellByPosition(DATE_COLUMN, row).getString()
        while date:
            f.write(date)
            for i in range(len(positions)):
                f.write(";" + str(sheet.getCellByPosition(DATE_COLUMN + i + 1, row).getValue()))
            f.write("\n")
            row += 1
            date = sheet.getCellByPosition(DATE_COLUMN, row).getString()


def _get_share_count(position: str):
    i = 0
    value = sheet.getCellByPosition(PORTFOLIO_IDENTIFIER_COLUMN,
                                    PORTFOLIO_FIRST_ROW + i).getString()
    while value:
        if value == position:
            return sheet.getCellByPosition(PORTFOLIO_SHARE_COUNT_COLUMN,
                                           PORTFOLIO_FIRST_ROW + i).getValue()
        i += 1
        value = sheet.getCellByPosition(PORTFOLIO_IDENTIFIER_COLUMN,
                                        PORTFOLIO_FIRST_ROW + i).getString()


def _get_positions():
    positions = []
    i = 1
    value = sheet.getCellByPosition(DATE_COLUMN + i, HEADER_ROW).getString()
    while value:
        positions.append(value)
        i += 1
        value = sheet.getCellByPosition(DATE_COLUMN + i, HEADER_ROW).getString()
    return positions