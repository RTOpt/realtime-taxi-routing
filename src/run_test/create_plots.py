import logging
import os

from src.utilities.visualization import (offline_plot, compare_algorithm_plot, compare_timeWindow_plot,
                                         number_scenarios)


def handle_create_plot(config_data, scenario: str):
    """Handle the create_plot task based on plot_name."""

    # Find the configuration for the specified scenario
    scenario_entry = next((entry for entry in config_data if entry.get("scenario") == scenario), None)
    if not scenario_entry:
        logging.error(f"Scenario '{scenario}' not found in config data.")
        return

    plot_entries = scenario_entry.get("plots", [])
    file_path = f"data/Instances/Results/{scenario}_simulation_results.csv"

    if not os.path.isfile(file_path):
        logging.error(f"Result file '{file_path}' does not exist.")
        return

    # Iterate over each plot configuration for the scenario
    for plot in plot_entries:
        plot_name = plot.get("plot_name")
        metrics = plot.get("metrics", [])

        if not plot_name:
            logging.warning(f"Plot entry without a plot_name found in scenario '{scenario}'. Skipping.")
            continue

        if plot_name == "offline_plot":
            offline_plot(file_path, metrics)
        elif plot_name == "compare_algorithm_plot":
            compare_algorithm_plot(file_path, metrics)
        elif plot_name == "compare_timeWindow_plot":
            compare_timeWindow_plot(file_path, metrics)
        elif plot_name == "number_scenarios":
            number_scenarios(file_path, metrics)
        else:
            logging.error(f"Unknown plot name '{plot_name}' in scenario '{scenario}'.")