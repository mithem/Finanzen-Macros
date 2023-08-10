"""Utility module to import all simulation types at once."""
from finance_macros.simulation.building_society_savings_contract import \
    BuildingSocietySavingsContract
from finance_macros.simulation.combination import Combination
from finance_macros.simulation.investment import InvestmentSimulation
from finance_macros.simulation.mortgage import MortgageSimulation
from finance_macros.simulation.overlay import Overlay
from finance_macros.simulation.real_estate import RealEstateSimulation


# just so that pylint doesn't complain about unused imports and the IDE doesn't remove them
def _():
    return [BuildingSocietySavingsContract, Combination, InvestmentSimulation, MortgageSimulation,
            Overlay, RealEstateSimulation]
