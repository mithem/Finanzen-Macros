"""Utilities for calculating the required stock acquisitions to match a target portfolio."""
import enum
import os
from typing import List, Union, Dict, Optional, Tuple


# Man, it sucks that you can't use external pip package with LibreOffice's Python interpreter :/
class TreeNode:
    position_type: "PositionType"
    parent: Optional["TreeNode"]
    children: List["TreeNode"]

    def __init__(self, position_type: "PositionType", children: List["TreeNode"] = None,
                 parent: Optional["TreeNode"] = None):
        self.position_type = position_type
        self.children = children if children is not None else []
        self.parent = parent
        for child in self.children:
            child.parent = self

    def __repr__(self):
        return f"TreeNode({self.position_type.value}, {self.children})"

    def find(self, position_type: "PositionType") -> Optional["TreeNode"]:
        if self.position_type == position_type:
            return self
        for child in self.children:
            found = child.find(position_type)
            if found:
                return found
        return None

    @property
    def descendents(self) -> List["TreeNode"]:
        return self.children + [descendent for child in self.children for descendent in
                                child.descendents]

    def __iter__(self):
        return iter(self.descendents + [self])


class PositionType(enum.Enum):
    """The type of a position."""
    POSITION_TYPE = "Position Type"
    STOCK = "Stock"
    INDEX_FUND = "Index Fund"
    INDIVIDUAL_STOCK = "Individual Stock"
    BOND = "Bond"
    GOVERNMENT_BOND = "Government Bond"
    CORPORATE_BOND = "Corporate Bond"
    IMMEDIATELY_AVAILABLE = "Immediately Available"
    CHECKING_ACCOUNT = "Checking Account"
    SAVINGS_ACCOUNT = "Savings Account"
    CASH = "Cash"
    FIXED_DEPOSIT = "Fixed Deposit"
    REAL_ESTATE = "Real Estate"

    @staticmethod
    def get_type_tree() -> TreeNode:
        def node(name: str, children: [TreeNode] = None) -> TreeNode:
            return TreeNode(PositionType(name), children=children)

        stock = node("Stock", children=[
            node("Index Fund"),
            node("Individual Stock")
        ])
        bond = node("Bond", children=[
            node("Government Bond"),
            node("Corporate Bond")
        ])
        immediately_available = node("Immediately Available", children=[
            node("Checking Account"),
            node("Savings Account"),
            node("Cash")
        ])
        fixed_deposit = node("Fixed Deposit")
        real_estate = node("Real Estate")
        children = [stock, bond, immediately_available, fixed_deposit, real_estate]
        return node("Position Type", children)

    def get_contained_types(self) -> List["PositionType"]:
        tree = PositionType.get_type_tree()
        type_node = tree.find(self)
        assert type_node is not None
        return [self] + list(map(lambda node: node.position_type, type_node.children))

    @staticmethod
    def get_all_types() -> List["PositionType"]:
        return [PositionType.STOCK, PositionType.INDEX_FUND, PositionType.INDIVIDUAL_STOCK,
                PositionType.BOND, PositionType.GOVERNMENT_BOND, PositionType.CORPORATE_BOND,
                PositionType.IMMEDIATELY_AVAILABLE, PositionType.CHECKING_ACCOUNT,
                PositionType.SAVINGS_ACCOUNT, PositionType.CASH, PositionType.FIXED_DEPOSIT,
                PositionType.REAL_ESTATE]

    def is_contained_in(self, other: "PositionType") -> bool:
        """Check if this position type is contained in another one."""
        return self in other.get_contained_types()

    @staticmethod
    def get_parent(type: "PositionType") -> Optional["PositionType"]:
        """Get the parent type of the given type."""
        tree = PositionType.get_type_tree()
        node = tree.find(type)
        return node.parent.position_type if node and node.parent else None


try:
    desktop = XSCRIPTCONTEXT.getDesktop()  # type: ignore
    model = desktop.getCurrentComponent()
    sheet = model.getSheets().getByName("Portfolio")
    EXPORT_DIRECTORY = sheet.getCellByPosition(30, 5).getString()

    PORTFOLIO_SUMMARY_COLUMN = 0
    PORTFOLIO_SUMMARY_ROW_START = 28
    PORTFOLIO_SUMMARY_POSITION_TYPES = [
        PositionType.STOCK,
        PositionType.INDEX_FUND,
        PositionType.IMMEDIATELY_AVAILABLE,
        PositionType.FIXED_DEPOSIT,
        PositionType.CASH
    ]

    PORTFOLIO_TABLE_ROW_START = 8
    PORTFOLIO_TABLE_COLUMNS = {
        "name": 0,
        "value": 9,
        "type": 11,
        "target_proportion_in_category": 13,
        "group": 14
    }

    PORTFOLIO_COMPOSITION_TARGET_TYPES_ROW_START = 8
    PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS = {
        "name": 16,
        "percentage": 17
    }

    PORTFOLIO_COMPOSITION_TARGET_GROUPS_ROW_START = 20

    PORTFOLIO_ACQUISITION_RECOMMENDATIONS_BUDGET_CELL = sheet.getCellByPosition(17, 32)
    PORTFOLIO_ACQUISITION_RECOMMENDATIONS_ROW_START = 37
    PORTFOLIO_ACQUISITION_RECOMMENDATIONS_COLUMNS = {
        "type": 16,
        "name": 17,
        "value": 18
    }

    PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_ROW_START = 37
    PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS = {
        "type": 20,
        "name": 21,
        "value": 22,
        "group": 23,
        "summary": 25
    }
except NameError:  # running tests
    import pandas as pd


class PositionGroup:
    """A group of positions (e.g. world regions)."""
    name: str

    @staticmethod
    def DEFAULT() -> "PositionGroup":
        return PositionGroup("Default")

    @property
    def display_value(self) -> str:
        return self.name if self != PositionGroup.DEFAULT() else ""

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, PositionGroup) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"PositionGroup({self.name})"


class Position:
    """A position in a portfolio."""
    type: PositionType
    name: str
    value: float
    group: PositionGroup

    def __init__(self, type: PositionType, name: str, value: float,
                 group: PositionGroup = PositionGroup.DEFAULT()):
        self.type = type
        self.name = name
        self.value = value
        self.group = group

    def __repr__(self):
        return f"{self.name} ({self.type.value}$): {round(self.value, 2)}"

    def __add__(self, other: Union["Position", "PositionAcquisition"]):
        if isinstance(other, Position):
            if self.type != other.type:
                raise ValueError("Cannot add positions of different types")
            if self.name != other.name:
                raise ValueError("Cannot add positions of different names")
            if self.group != other.group:
                raise ValueError("Cannot add positions of different groups")
            return PositionAcquisition(
                Position(self.type, self.name, self.value + other.value, self.group),
                other.value)
        if isinstance(other, PositionAcquisition):
            if self.type != other.position.type:
                raise ValueError("Cannot add positions of different types")
            if self.name != other.position.name:
                raise ValueError("Cannot add positions of different names")
            if self.group != other.position.group:
                raise ValueError("Cannot add positions of different groups")
            return Position(self.type, self.name, self.value + other.amount, self.group)
        raise ValueError(f"Cannot add Position and {type(other)}")


class PositionAcquisition:
    """An acquisition of a position."""
    position: Position
    amount: float

    def __init__(self, position: Position, amount: float):
        self.position = position
        self.amount = amount

    def __repr__(self):
        return f"{self.position.name} ({self.position.type.value}$): {round(self.amount, 2)}"


class PortfolioCompositionTarget:
    """A target portfolio composition."""
    TypeComposition = Dict[PositionType, float]
    PositionComposition = Dict[str, float]
    GroupComposition = Dict[PositionGroup, float]

    # Composition target for each position type (type is key)
    type_composition: TypeComposition
    # Composition target for each position (name is key)
    position_composition: PositionComposition
    group_composition: GroupComposition

    def __init__(
            self,
            type_composition: TypeComposition,
            position_composition: Dict[str, float],
            current_composition: "PortfolioComposition",
            group_composition: GroupComposition
    ):
        self.type_composition = PortfolioCompositionTarget.process_target_type_composition(
            type_composition, current_composition)
        self.position_composition = position_composition
        self.group_composition = group_composition

    @staticmethod
    def process_target_type_composition(
            type_composition: "PortfolioCompositionTarget.TypeComposition",
            current_composition: "PortfolioComposition"
    ) -> TypeComposition:
        """Validate the target type composition and ensure that child categories are scaled
        according to their current proportions if only their parent category/type is specified."""
        composition = type_composition
        current = current_composition.get_portfolio_composition()
        tree = PositionType.get_type_tree()
        for node in tree:
            if node.position_type in type_composition:
                # If the type's children are not specified in the target composition
                if len(node.descendents) > 0 and all(
                        descendent.position_type not in type_composition for descendent in
                        node.descendents):
                    # Scale the children according to their current proportions
                    for descendent in node.descendents:
                        composition[descendent.position_type] = current.get(
                            descendent.position_type, 0) / current.get(node.position_type) * \
                                                                composition[node.position_type]

        not_specified_types = set(PositionType.get_all_types()) - (set(composition.keys()) | set(
            contained_type for type in composition.keys() for contained_type in
            type.get_contained_types()))
        current_proportion_of_specified_types = sum(
            map(lambda type: current.get(type, 0), type_composition.keys()))
        target_proportion_of_specified_types = sum(type_composition.values())
        # Scale the not specified types according to their current proportions but within the
        # boundaries of the specified types
        k = current_proportion_of_specified_types / target_proportion_of_specified_types
        for type in not_specified_types:
            composition[type] = current.get(type, 0) * k
        return composition


class PortfolioComposition:
    """A portfolio composition."""
    positions: List[Position]

    def __init__(self, positions: List[Position]):
        self.positions = positions

    @staticmethod
    def load_from_csv(filename: str) -> "PortfolioComposition":
        """Load a portfolio composition from a csv file"""
        data = pd.read_csv(filename, delimiter=";")
        groups = []
        positions = []
        for row in data.iterrows():
            row = row[1]
            matching_groups = list(filter(lambda group: group.name == row["Gruppe"], groups))
            if len(matching_groups) > 0:
                group = matching_groups[0]
            elif not pd.isnull(row["Gruppe"]):
                group = PositionGroup(row["Gruppe"])
                groups.append(group)
            else:
                group = PositionGroup.DEFAULT()
            position = Position(
                PositionType(row["Kategorie"]),
                row["Name"],
                row["Wert"],
                group
            )
            positions.append(position)
        return PortfolioComposition(positions)

    def get_portfolio_composition(self) -> PortfolioCompositionTarget.TypeComposition:
        """Get the portfolio composition. (percentage of portfolio value per position type)"""
        total_value = self.get_total_value()
        return {key: value / total_value for key, value in
                self.get_position_type_value_composition().items()}

    def get_position_type_value_composition(self) -> PortfolioCompositionTarget.TypeComposition:
        """Get the portfolio composition. (value of each position type)"""
        return {position_type: sum(  # sum of position values for each type
            map(lambda position: position.value,  # position value for each type
                # only for positions of the type
                filter(lambda position: position.type.is_contained_in(position_type),
                       self.positions)
                )) for position_type in PositionType.get_all_types()}

    def get_group_composition(self) -> PortfolioCompositionTarget.GroupComposition:
        """Get the portfolio group composition. (percentage of portfolio value per position group)"""
        total_value = self.get_total_value()
        return {key: value / total_value for key, value in
                self.get_group_value_composition().items()}

    def get_group_value_composition(self) -> PortfolioCompositionTarget.GroupComposition:
        """Get the portfolio group composition as group value heights."""
        all_groups = set(map(lambda position: position.group, self.positions)) | {
            PositionGroup.DEFAULT()}
        return {position_group: sum(  # sum of position proportions for each group
            map(lambda position: position.value,  # position proportion for each group
                # only for positions of the group
                filter(lambda position: position.group == position_group,
                       self.positions)
                )) for position_group in all_groups}

    def get_total_value(self, position_type: Optional[PositionType] = None):
        return sum(map(lambda position: position.value, filter(
            lambda position: position_type is None or position.type.is_contained_in(position_type),
            self.positions)))

    def get_total_value_of_group(self, group: PositionGroup):
        return sum(map(lambda position: position.value, filter(
            lambda position: position.group == group,
            self.positions)))

    def __add__(self, other):
        if isinstance(other, Position):
            return PortfolioComposition(self.positions + [other])
        elif isinstance(other, PositionAcquisition):
            positions = list(filter(lambda position: position.type == other.position.type and
                                                     position.name == other.position.name,
                                    self.positions))
            if len(positions) == 0:
                return PortfolioComposition(self.positions + [other.position])
            elif len(positions) == 1:
                new_position = positions[0] + other
                idx = self.positions.index(positions[0])
                new_positions = self.positions.copy()
                new_positions[idx] = new_position
                return PortfolioComposition(new_positions)
            else:
                raise ValueError("Multiple positions with the same type and name.")
        elif isinstance(other, list):
            if len(other) == 0:
                return self
            return (self + other[0]) + other[1:]
        else:
            raise ValueError(f"Cannot add PortfolioComposition and {type(other)}")

    def __str__(self):
        return "\n".join(map(str, self.positions))

    def get_required_acquisitions(self, target: PortfolioCompositionTarget, budget: float) -> Tuple[
        List[
            PositionAcquisition],
        "PortfolioComposition"]:
        """Get the required acquisitions to match a target portfolio composition (within the `budget`)."""
        current_total_value = self.get_total_value()
        new_total_value = current_total_value + budget
        current_composition = self.get_portfolio_composition()
        current_group_composition = self.get_group_composition()

        # Stage 1: Calculate the required acquisitions for each position type
        acquisition_budget_by_type = {}
        for position_type, target_proportion in target.type_composition.items():
            current_proportion = current_composition.get(position_type, 0)
            target_value = new_total_value * target_proportion
            current_value = current_total_value * current_proportion
            required_value = target_value - current_value
            acquisition_budget_by_type[position_type] = required_value

        # Stage 2: Calculate the required acquisitions for each position group
        acquisition_budget_by_group = {}
        for position_group, target_proportion in target.group_composition.items():
            current_proportion = current_group_composition.get(position_group, 0)
            position_type = \
                list(filter(lambda pos: pos.group == position_group,
                            self.positions))[0].type
            target_proportion_of_category = target.type_composition.get(position_type,
                                                                        current_composition.get(
                                                                            position_type))
            target_value = new_total_value * target_proportion * target_proportion_of_category
            current_value = current_total_value * current_proportion
            required_value = target_value - current_value
            acquisition_budget_by_group[
                position_group] = required_value

        # Stage 3: Calculate the required acquisitions for each position
        acquisitions = []
        for position in self.positions:
            current_proportion_in_category = position.value / (
                    current_composition.get(position.type,
                                            position.value) * current_total_value)
            target_proportion_in_category = target.position_composition.get(position.name,
                                                                            current_proportion_in_category)
            target_proportion_of_category = target.type_composition.get(position.type,
                                                                        current_composition.get(
                                                                            position.type))
            target_value = new_total_value * target_proportion_of_category * target_proportion_in_category
            current_value = position.value
            requested = target_value - current_value
            group_budget = acquisition_budget_by_group.get(position.group,
                                                           requested) if position.group != PositionGroup.DEFAULT() else requested
            required_value = requested * acquisition_budget_by_type.get(position.type,
                                                                        requested) * group_budget
            acquisitions.append(PositionAcquisition(position, required_value))

        # Stage 4: Normalize acquisitions to fit into the budget
        budget_required = sum(map(lambda acquisition: acquisition.amount, acquisitions))
        normalized_acquisitions = []
        for acquisition in acquisitions:
            normalized_amount = acquisition.amount / budget_required * budget
            normalized_acquisitions.append(PositionAcquisition(acquisition.position,
                                                               normalized_amount))

        return normalized_acquisitions, self + normalized_acquisitions


def _load_portfolio_composition() -> PortfolioComposition:
    """Load the portfolio composition."""
    positions = []
    row = PORTFOLIO_TABLE_ROW_START
    cell = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["name"], row)
    name = cell.getString()
    while name:
        value = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["value"], row).getValue()
        type = PositionType(
            sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["type"], row).getString())
        groupValue = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["group"], row).getString()
        group = PositionGroup(groupValue) if groupValue else PositionGroup.DEFAULT()
        positions.append(Position(type, name, value, group))
        row += 1
        cell = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["name"], row)
        name = cell.getString()

    return PortfolioComposition(positions)


def _load_portfolio_composition_target() -> PortfolioCompositionTarget:
    """Load the portfolio composition target"""
    # Step 1: Load target composition for each category
    type_targets = {}
    row = PORTFOLIO_COMPOSITION_TARGET_TYPES_ROW_START
    cell = sheet.getCellByPosition(PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["name"],
                                   row)
    type_name = cell.getString()
    while type_name and type_name != "Gruppen":
        percentage = sheet.getCellByPosition(
            PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["percentage"], row).getValue()
        type = PositionType(type_name)
        type_targets[type] = percentage
        row += 1
        cell = sheet.getCellByPosition(
            PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["name"], row)
        type_name = cell.getString()

    # Step 2: Load target composition for each group
    group_targets = {}
    row = PORTFOLIO_COMPOSITION_TARGET_GROUPS_ROW_START
    cell = sheet.getCellByPosition(PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["name"],
                                   row)
    group_name = cell.getString()
    while group_name:
        percentage = sheet.getCellByPosition(
            PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["percentage"], row).getValue()
        group = PositionGroup(group_name)
        group_targets[group] = percentage
        row += 1
        cell = sheet.getCellByPosition(
            PORTFOLIO_COMPOSITION_TARGET_TYPES_AND_GROUPS_COLUMNS["name"], row)
        group_name = cell.getString()

    # Step 3: Load target composition for each position
    position_targets = {}
    row = PORTFOLIO_TABLE_ROW_START
    cell = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["name"], row)
    name = cell.getString()
    while name:
        proportion_cell = sheet.getCellByPosition(
            PORTFOLIO_TABLE_COLUMNS["target_proportion_in_category"],
            row)
        if proportion_cell.getString() != "":
            target_proportion_in_category = proportion_cell.getValue()
            position_targets[name] = target_proportion_in_category
        row += 1
        cell = sheet.getCellByPosition(PORTFOLIO_TABLE_COLUMNS["name"], row)
        name = cell.getString()

    current_composition = _load_portfolio_composition()
    return PortfolioCompositionTarget(type_targets, position_targets, current_composition,
                                      group_targets)


def write_portfolio_summary(*args, **kwargs):
    """Write a summary of the portfolio."""
    composition = _load_portfolio_composition()
    _write_summary_for_portfolio(composition, PORTFOLIO_SUMMARY_COLUMN, PORTFOLIO_SUMMARY_ROW_START)


def _write_summary_for_portfolio(composition: PortfolioComposition, start_col: int, start_row: int):
    type_composition = composition.get_portfolio_composition()
    group_composition = composition.get_group_composition()
    for row, type in enumerate(PORTFOLIO_SUMMARY_POSITION_TYPES):
        value = composition.get_total_value(type)
        sheet.getCellByPosition(start_col + 1,
                                start_row + row).setValue(value)
    row_idx = len(PORTFOLIO_SUMMARY_POSITION_TYPES) + start_row + 1
    _clear_cells(row_idx, start_col, 25)
    _clear_cells(row_idx, start_col + 1, 25)
    for type, proportion in type_composition.items():
        sheet.getCellByPosition(start_col, row_idx).setString(type.value)
        sheet.getCellByPosition(start_col + 1, row_idx).setValue(proportion)
        sheet.getCellByPosition(start_col + 2, row_idx).setValue(composition.get_total_value(type))
        row_idx += 1
    row_idx += 1
    for group, proportion in group_composition.items():
        sheet.getCellByPosition(start_col, row_idx).setString(
            group.name)
        sheet.getCellByPosition(start_col + 1, row_idx).setValue(proportion)
        sheet.getCellByPosition(start_col + 2, row_idx).setValue(
            composition.get_total_value_of_group(group))
        row_idx += 1


def _clear_cells(row_start: int, column: int, count: int):
    for row in range(row_start, row_start + count):
        sheet.getCellByPosition(column, row).setString("")


def write_portfolio_acquisition_recommendations(*args, **kwargs):
    """Write the portfolio acquisition recommendations."""
    for column in PORTFOLIO_ACQUISITION_RECOMMENDATIONS_COLUMNS.values():
        _clear_cells(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_ROW_START, column, 25)
    composition = _load_portfolio_composition()
    target = _load_portfolio_composition_target()
    budget = PORTFOLIO_ACQUISITION_RECOMMENDATIONS_BUDGET_CELL.getValue()
    acquisition_recommendations, resulting_composition = composition.get_required_acquisitions(
        target, budget)
    row = PORTFOLIO_ACQUISITION_RECOMMENDATIONS_ROW_START
    for row_idx, acquisition in enumerate(acquisition_recommendations):
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_COLUMNS["type"],
                                row + row_idx).setString(acquisition.position.type.value)
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_COLUMNS["name"],
                                row + row_idx).setString(acquisition.position.name)
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_COLUMNS["value"],
                                row + row_idx).setValue(acquisition.amount)
    write_recommendations_resulting_portfolio(resulting_composition)


def write_recommendations_resulting_portfolio(composition: PortfolioComposition):
    for column in PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS.values():
        _clear_cells(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_ROW_START, column,
                     25)
    row = PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_ROW_START
    for row_idx, position in enumerate(composition.positions):
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS[
                                    "type"],
                                row + row_idx).setString(position.type.value)
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS[
                                    "name"],
                                row + row_idx).setString(position.name)
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS[
                                    "value"],
                                row + row_idx).setValue(position.value)
        sheet.getCellByPosition(PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS[
                                    "group"],
                                row + row_idx).setString(position.group.display_value)
    _write_summary_for_portfolio(composition,
                                 PORTFOLIO_ACQUISITION_RECOMMENDATIONS_RESULTING_PORTFOLIO_COLUMNS[
                                     "summary"],
                                 row)


def export_portfolio(*args, **kwargs):
    """Export the portfolio to a csv file."""
    composition = _load_portfolio_composition()
    with open(os.path.join(EXPORT_DIRECTORY, "portfolio.csv"), "w", encoding="utf-8") as file:
        file.write("Gruppe;Kategorie;Name;Wert\n")
        for position in composition.positions:
            file.write(
                f"{position.group.display_value};{position.type.value};{position.name};{position.value}\n")


if __name__ == "__main__":
    gWorld = PositionGroup("World")
    gUS = PositionGroup("US")
    gEurope = PositionGroup("Europe")

    composition = PortfolioComposition([
        Position(PositionType.INDEX_FUND, "iShares MSCI Europe SRI", 7198.35, gEurope),
        Position(PositionType.INDEX_FUND, "UBS MSCI World SRI", 7527.42, gWorld),
        Position(PositionType.INDEX_FUND, "Vanguard S+P 500", 7925.45, gUS),
        Position(PositionType.INDIVIDUAL_STOCK, "BYD Co.", 321.2),
        Position(PositionType.INDEX_FUND, "Vanguard FTSE DEV.EU", 390.31, gEurope),
        Position(PositionType.INDEX_FUND, "Lyxor Net Zero 2050 S&P 500", 195.31, gUS),
        Position(PositionType.SAVINGS_ACCOUNT, "Savings account", 3115.09),
        Position(PositionType.CHECKING_ACCOUNT, "Checking account", 255),
        Position(PositionType.FIXED_DEPOSIT, "Fixed deposit", 3000.29)
    ])
    comp = composition.get_portfolio_composition()

    target = PortfolioCompositionTarget({
        PositionType.FIXED_DEPOSIT: .1,
        PositionType.IMMEDIATELY_AVAILABLE: .110573
    },
        {},
        composition, {
            gWorld: .34,
            gUS: .33,
            gEurope: .33
        }
    )
    acquisitions, new_composition = composition.get_required_acquisitions(target, 500)
    print("Necessary acquisitions: " + str(acquisitions))
    print("New composition: " + str(new_composition))
