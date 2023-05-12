"""Utility for refreshing stock quotes in the spreadsheet."""

# mypy: ignore-errors
desktop = XSCRIPTCONTEXT.getDesktop()  # pylint: disable=undefined-variable
model = desktop.getCurrentComponent()
sheet = model.getSheets().getByName("Sparen")


def ReloadStockQuotes(*args):  # pylint: disable=invalid-name,unused-argument
    """Toggle the identifier copy mode cell to trigger a reload of stock quotes."""
    cell = sheet.getCellByPosition(4, 30)
    cell.setString("erase")
    cell.setString("copy")
