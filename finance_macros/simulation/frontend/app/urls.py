from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("export-viewer", views.export_viewer, name="export-viewer"),
    path("simulation-view", views.simulation_view, name="simulation-view"),
    path("additional-args", views.additional_args, name="additional-args"),
    path("simulate", views.simulate, name="simulate"),
    path("simulation-results", views.get_simulation_results, name="get-simulation-results"),
    path("reset-context", views.reset_context, name="reset-context"),
]
