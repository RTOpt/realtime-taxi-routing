import os
import logging
import pandas as pd

from src.utilities import SolutionMode, Algorithm, Objectives, print_dict_as_table
from src.run_simulation import run_simulation


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    # define paths
    base_folder = "data/Instances"
    graph_file_path = "data/Instances/network.json"

    # Settings
    """
    solution_mode : The mode of solution,
        - offline : all the requests revealed at the start (release time = 0 for all requests)
        - fully_online : release time is equal to the ready time for all requests
        - online : requests are known 30 minutes before the ready time
    algorithm: Algorithm used to optimize the plan:
        - MIP_SOLVER : using the Gurobi MIP solver to solve the problem
        - GREEDY : greedy approach to assign requests to vehicles          
    """
    algorithm = Algorithm.MIP_SOLVER
    solution_mode = SolutionMode.OFFLINE
    # time window in minute
    time_windows = [1, 3, 6]

    results = []

    # Iterate over each test folder and each objective
    for test_folder in os.listdir(base_folder):
        test_path = os.path.join(base_folder, test_folder)
        if os.path.isdir(test_path):
            for objective in Objectives:
                for time_window in time_windows:
                    trips_count, vehicles_count, output_dict = run_simulation(test_path, graph_file_path, algorithm,
                                                                              objective, solution_mode, time_window)
                    # Prepare results
                    info_dict = {
                        'Test': test_folder,
                        '# Trips': trips_count,
                        '# Vehicles': vehicles_count,
                        'Time window (min)': time_window,
                        'Solution Mode': solution_mode.value,
                    }

                    results.append({**info_dict, **output_dict})

                    # print solution
                    print_dict_as_table(results[-1])

    # Convert results to DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(by=['# Trips', 'Time window (min)', 'Objective'])

    # Save DataFrame to CSV
    csv_file_path = "data/Instances/simulation_results.csv"
    df.to_csv(csv_file_path, index=False)

    # Print results
    with pd.option_context('display.colheader_justify', 'center'):
        print(df.to_markdown(tablefmt="pipe", headers="keys"))
