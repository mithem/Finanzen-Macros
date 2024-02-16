"""Django fm-filters for use in the templates."""
import re
from typing import Optional

from django import template

from finance_macros.simulation.combination import CombinationFunctionList
from finance_macros.simulation.config import CLIArgument
from finance_macros.simulation.core import SimulationContext

register = template.Library()


@register.filter(name="get_user_prompt")
def arg_get_user_prompt(arg: CLIArgument, context: SimulationContext):
    """Get the user's prompt."""
    return arg.get_user_prompt(context)


@register.filter(name="match")
def match(string: str, regex: str) -> Optional[re.Match]:
    """Match the string against the regex."""
    return re.match(regex, string)


@register.filter(name="match_promptable")
def match_promptable(string: str) -> Optional[str]:
    """Match to see if the string matches a promptable string"""
    m = match(string, r'<Promptable type="(?P<type>.+)"/>')
    return m.group("type") if m else None


@register.filter(name="get_promptable_args")
def get_promptable_args(for_type: str):
    """Get the promptable arguments for the given type."""
    match for_type:
        case "CombinationFunctionList":
            return CombinationFunctionList().args
        case other:
            raise ValueError(f"Invalid type: '{other}'")


@register.filter(name="replacing")
def replacing(string: str, regex_and_replacement: str) -> str:
    """Replace the given string with the given regex_and_replacement."""
    regex, replacement = regex_and_replacement.split("::")
    return re.sub(regex, replacement, string)
