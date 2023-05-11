"""Snapshot function for net worth history table."""
import datetime

DATE_COLUMN = 4
NET_WORTH_COLUMN = 5
DATE_FORMAT = "%d.%m.%Y"

# mypy: ignore-errors
desktop = XSCRIPTCONTEXT.getDesktop()  # pylint: disable=undefined-variable
model = desktop.getCurrentComponent()
sheet = model.getSheets().getByName("Sparen")


def SnapshotNetWorth(*args):  # pylint: disable=invalid-name,unused-argument
    """Snapshot the current net worth and add it to the net worth history table."""

    def get_date_value(row: int) -> str:
        return sheet.getCellByPosition(DATE_COLUMN, row).getString()

    row = 55
    date = get_date_value(row)
    while date:
        row += 1
        date = get_date_value(row)

    today = datetime.date.today()
    current_net_worth = sheet.getCellByPosition(NET_WORTH_COLUMN, 49).getValue()

    sheet.getCellByPosition(DATE_COLUMN, row).setString(today.strftime(DATE_FORMAT))
    sheet.getCellByPosition(NET_WORTH_COLUMN, row).setValue(current_net_worth)
