import os
import logging
import pandas as pd

from src.utilities import SolutionMode, Algorithm, Objectives, print_dict_as_table
from src.run_simulation import run_taxi_simulation


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.WARN)  # INFO

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
        - RANDOM : random algorithm to assign arrival requests to vehicles
        - RANKING : ranking method to assign arrival requests to vehicles  
        - QUALITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            a counter is incremented for the best request to assign at each scenario.
        - QUANTITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            he best request to assign is credited by the optimal solution value, rather than merely incrementing a counter.  
    """
    algorithms = [Algorithm.GREEDY, Algorithm.RANDOM, Algorithm.RANKING]
    solution_modes = [SolutionMode.ONLINE, SolutionMode.FULLY_ONLINE]
    objectives = [Objectives.WAIT_TIME, Objectives.PROFIT, Objectives.TOTAL_CUSTOMERS]
    # time window in minute
    time_windows = [1, 3, 6]

    results = []

    # Iterate over each test folder, objective
    for test_folder in os.listdir(base_folder):
        test_path = os.path.join(base_folder, test_folder)
        if os.path.isdir(test_path):
            for algorithm in algorithms:
                for solution_mode in solution_modes:
                    for objective in objectives:
                        for time_window in time_windows:
                            try:
                                print("==================================================")
                                print("Run taxi simulation with:")
                                print("  Instance:", test_folder)
                                print("  Algorithm:", algorithm.value)
                                print("  Objective:", objective.value)
                                print("  Solution mode:", solution_mode.value)
                                print("  Time window (min):", time_window)
                                print("==================================================")
                                info_dict, output_dict = run_taxi_simulation(
                                    test_path, graph_file_path, algorithm, objective, solution_mode, time_window)
                            except Exception as e:
                                print(e)
                                continue

                            # print solution
                            results.append({**info_dict, **output_dict})
                            print_dict_as_table(results[-1])

    # Convert results to DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values(by=['# Trips', 'Time window (min)'])

    # Save DataFrame to CSV
    csv_file_path = "data/Instances/simulation_results.csv"
    df.to_csv(csv_file_path, index=False)

    # Print results
    with pd.option_context('display.colheader_justify', 'center'):
        print(df.to_markdown(tablefmt="pipe", headers="keys"))
