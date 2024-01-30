import os
import logging
from src.utilities import SolutionMode, Algorithm, Objectives, print_dict_as_table
from src.run_simulation import run_simulation


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    # Define base paths
    base_folder = "data/Instances"
    graph_file_path = "data/Instances/network.json"
    test_folder = "High_3"
    test_path = os.path.join(base_folder, test_folder)

    # Define simulation settings
    """
    objective: The optimization objective to achieve 
        - total_Profit: total profit of served requests
        - waiting_time: total wait time of served requests
        - total_customers: total number of served customers
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
    objective = Objectives.TOTAL_CUSTOMERS
    time_window = 3  # Time window in minutes


    # Run the simulation
    trips_count, vehicles_count, output_dict = run_simulation(test_path, graph_file_path, algorithm,
                                                              objective, solution_mode, time_window)
    # Compile information about the test and results
    info_dict = {
        'Test': test_folder,
        '# Trips': trips_count,
        '# Vehicles': vehicles_count,
        'Time window (min)': time_window,
        'Solution Mode': solution_mode.value,
    }

    result = {**info_dict, **output_dict}

    # print solution
    print_dict_as_table(result)

