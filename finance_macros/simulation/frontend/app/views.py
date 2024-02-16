"""Django views."""
import json
import urllib
import urllib.parse
from typing import Dict

import pandas as pd
from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.shortcuts import render, redirect

import finance_macros.simulation.export_viewer as export_viewer_module
from finance_macros.simulation import config
from finance_macros.simulation import core
from finance_macros.simulation import graphs
from finance_macros.simulation import main
from finance_macros.simulation.config import CLIArgumentLibrary
from finance_macros.simulation.core import SimulationContext, Simulation
from finance_macros.simulation.export_viewer import load_data

CONFIG = config.Config()
ALL_SIMULATION_TYPES = CONFIG.get_simulation_types()
CONTEXT = SimulationContext()


def insert_into_iframe(html):
    """Inserts the HTML code inside an iframe returned as html code"""
    return "<iframe srcdoc='" + html + "'></iframe>"


raw_data = load_data("/Users/miguel/Desktop")
data = {sim: {"table_html": insert_into_iframe(graphs.get_table(values).to_html()),
              "graph_html": insert_into_iframe(graphs.get_line_plot(values).to_html())}
        for sim, values in raw_data.items()}

print("loaded data.")


def get_cli_arg_types_for_context() -> Dict:
    """Get the CLI argument data types, for use in a Django context."""
    sim_types = CONFIG.get_simulation_types()
    data_types = {arg.type for sim_type in sim_types for arg in sim_type.args}
    return {
        type_: type_ for type_ in data_types
    }


# Create your views here.
def index(request):
    """The start page."""
    context = {
        "simulation_types": ALL_SIMULATION_TYPES,
    }
    return render(request, "app/index.html", context)


def export_viewer(request):
    """The export viewer page."""
    # return HttpResponse("Type: " + escape(str(type(data))))
    return render(request, "app/export_viewer.html", {"export_data": {}})


def simulation_view(request):
    """The page that shows the simulation view."""
    sim_type = request.GET.get("simulation_type", None)
    try:
        simulation_type = CONFIG.get_simulation_type(sim_type)
        context = {
            "simulation_types": ALL_SIMULATION_TYPES,
            "simulation_type": simulation_type,
            **get_cli_arg_types_for_context(),
            "args_json": json.dumps(
                [{"key": arg.key, "display_name": arg.display_name,
                  "type": arg.type_name} for arg
                 in simulation_type.args]),
            "simulation_context": CONTEXT
        }
        return render(request, "app/simulation-view.html", context)
    except core.UserError as exc:
        raise BadRequest(f"Invalid simulation type '{sim_type}'.") from exc


def additional_args(request):
    """"Return to the frontend whether there are additional arguments that
    need to be entered by the user."""
    args_data = json.loads(urllib.parse.unquote(request.GET.get("args", "[]")))
    entered_args = list(map(lambda arg: (CLIArgumentLibrary.get_argument(arg["key"]), arg["value"]),
                            args_data))
    additional_arguments = []
    for arg, value in entered_args:
        if arg.additional_arg_provider:
            value, add_args = arg.load_value(CONTEXT, lambda _, __: value)
            if add_args:
                additional_arguments.extend(add_args)

    arg_dicts = list(map(lambda arg: {"key": arg.key, "display_name": arg.display_name,
                                      "type": arg.type_name}, additional_arguments))
    return JsonResponse({"additional_args": arg_dicts})


def simulate(request):
    """The endpoint to run and save a simulation"""
    arguments = map(lambda arg: (CLIArgumentLibrary.get_argument(arg["key"]), arg["value"]),
                    json.loads(urllib.parse.unquote(request.GET.get("args", "[]"))))
    args = {
        arg.key: arg.load_value(CONTEXT, lambda _, __: value)[0] for arg, value in
        arguments
    }
    export_dir = request.GET.get("export_dir", "/Users/miguel/Desktop")
    simulation_type = request.GET.get("simulation_type", None)
    sim_type = CONFIG.get_simulation_type(simulation_type)
    identifier = sim_type.key
    sim: Simulation = sim_type.type(export_directory=export_dir, identifier=identifier,
                                    context=CONTEXT, **args)
    sim.simulate()
    sim.write_csv()
    return JsonResponse({"success": True, "identifier": sim.identifier})


def load_simulation_data(sim_data: Dict, identifier: str) -> pd.DataFrame:
    """Load simulation data and return it as a dataframe"""
    try:
        return sim_data[identifier]
    except KeyError as exc:
        short_id = Simulation.make_short_identifier(identifier)
        for key, dataframe in sim_data.items():
            if Simulation.make_short_identifier(key) == short_id:
                return dataframe
        raise FileNotFoundError(f"Simulation with identifier '{identifier}' not found.") from exc


def get_simulation_results(request):
    """Get the results of a simulation."""
    identifier = request.GET.get("identifier", None)
    if identifier is None:
        raise BadRequest("No identifier specified")
    export_dir = request.GET.get("export_dir", "/Users/miguel/Desktop")
    sim_data = load_simulation_data(export_viewer_module.load_data(export_dir), identifier)
    line_data = []
    for col in sim_data.columns:
        if col == "date":
            continue
        line_data.append(
            {
                "name": col,
                "x": sim_data["date"].tolist(),
                "y": sim_data[col].tolist(),
                "type": "line"
            }
        )
    table_data = [{
        "type": "table",
        "header": {
            "values": sim_data.columns.tolist(),
        },
        "cells": {
            "values": [sim_data[col].tolist() for col in sim_data.columns]
        }
    }]
    res = JsonResponse({
        "success": True,
        "data": {
            "line": line_data,
            "table": table_data
        }
    })
    res.content = res.content.replace(b"NaN", b"null")
    return res


def reset_context(request):
    """Reset the context of already run simulations"""
    CONTEXT.reset()
    main.delete_existing("/Users/miguel/Desktop")
    url = request.GET.get("redirect_url", "index")
    return redirect(url)
