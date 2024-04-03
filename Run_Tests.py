import os
import logging
import pandas as pd

from src.utilities import SolutionMode, Algorithm, Objectives, DestroyMethod, print_dict_as_table
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
            he best request to assign is credited by the optimal solution value, rather than merely incrementing a 
            counter. 
        - RE_OPTIMIZE: Algorithm to re-optimize the solution based on destroy and repair
        
    destroy_method: Method used for destruction in re-optimizing
        - DEFAULT: Default destruction method (Complete re-optimization)
        - FIX_VARIABLES: fix some of the variables in the model
        - FIX_ARRIVALS: fix a time window around the arrival time
        - BONUS: arbitrary destroy method as bonus
    """
    # set the algorithm to test
    algorithms = [Algorithm.RE_OPTIMIZE]

    # set the solution mode
    solution_modes = [SolutionMode.ONLINE, SolutionMode.PARTIAL]
    destroy_methods = [DestroyMethod.FIX_VARIABLES, DestroyMethod.FIX_ARRIVALS, DestroyMethod.DEFAULT]

    objectives = [Objectives.PROFIT]

    # time window in minute
    time_windows = [6]
    known_portions = [0.25, 0.5]
    cust_node_hour = 0.2
    nb_scenario = 5

    results = []

    # Iterate over each test folder, objective
    for test_folder in os.listdir(base_folder):
        test_path = os.path.join(base_folder, test_folder)
        if os.path.isdir(test_path):
            for algorithm in algorithms:
                for solution_mode in solution_modes:
                    for objective in objectives:
                        for time_window in time_windows:
                            for destroy_method in destroy_methods:
                                known_portions_to_run = known_portions if solution_mode == SolutionMode.PARTIAL else [0]
                                for known_portion in known_portions_to_run:
                                    try:
                                        print("==================================================")
                                        print("Run taxi simulation with:")
                                        print("  Instance:", test_folder)
                                        print("  Algorithm:", algorithm.value)
                                        print("  Objective:", objective.value)
                                        print("  Solution mode:", solution_mode.value)
                                        print("  Time window (min):", time_window)
                                        print("  Percentage known (%):", known_portion)
                                        if algorithm in [Algorithm.QUALITATIVE_CONSENSUS , Algorithm.QUANTITATIVE_CONSENSUS]:
                                            print("  Number of Scenario:", nb_scenario)
                                            print("  customers per node per hour:", cust_node_hour)
                                        print("==================================================")
                                        info_dict, output_dict = run_taxi_simulation(
                                            test_path, graph_file_path, algorithm, objective, solution_mode, time_window,
                                            destroy_method, nb_scenario, cust_node_hour, known_portion)

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
