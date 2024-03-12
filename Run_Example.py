import os
import logging
import argparse
import difflib
from src.utilities import SolutionMode, Algorithm, Objectives, print_dict_as_table
from src.run_simulation import run_taxi_simulation


def run_example(test_folder="Med_1",
                objective=Objectives.TOTAL_CUSTOMERS,
                time_window_min=3,
                algorithm=Algorithm.MIP_SOLVER,
                solution_mode=SolutionMode.OFFLINE,
                cust_node_hour=0.35,
                nb_scenario=20,
                known_portion=0):
    """
    test_folder: folder of the instance to test
    objective: The optimization objective to achieve
        - total_Profit: total profit of served requests
        - waiting_time: total wait time of served requests
        - total_customers: total number of served customers
    time_window_min: size of the time window in minutes to serve a request
    solution_mode : The mode of solution,
        - offline : all the requests revealed at the start (release time = 0 for all requests)
        - fully_online : release time is equal to the ready time for all requests
        - online : requests are known 30 minutes before the ready time
        - partial : a portion of requests are known at the start and for the rest release time is equal to the ready time
    algorithm: Algorithm used to optimize the plan:
        - MIP_SOLVER : using the Gurobi MIP solver to solve the problem
        - GREEDY : greedy approach to assign requests to vehicles
	    - RANDOM : random algorithm to assign arrival requests to vehicles
        - RANKING : ranking method to assign arrival requests to vehicles
        - QUALITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            a counter is incremented for the best request to assign at each scenario.
        - QUANTITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            he best request to assign is credited by the optimal solution value, rather than merely incrementing a counter.
    cust_node_hour: the average rate of customers per node (in the network) per hour
        - for small size tests select 0.2
        - for medium size tests select 0.3
        - for large size tests select 0.7
    nb_scenario: Total number of scenarios to be solved for consensus
    known_portion: portion of requests that are known in advance
    """
    logging.getLogger().setLevel(logging.WARN)  # INFO

    # Define base paths
    base_folder = "data/Instances"
    graph_file_path = "data/Instances/network.json"
    test_path = os.path.join(base_folder, test_folder)

    # Display args
    print("==================================================")
    print("Run taxi simulation with:")
    print("  Instance:", test_folder)
    print("  Algorithm:", algorithm.value)
    print("  Objective:", objective.value)
    print("  Solution mode:", solution_mode.value)
    print("  Time window (min):", time_window_min)
    print("  Percentage known (%):", known_portion)
    if algorithm == Algorithm.QUALITATIVE_CONSENSUS or algorithm == Algorithm.QUANTITATIVE_CONSENSUS:
        print("  Number of Scenario:", nb_scenario)
        print("  customers per node per hour:", cust_node_hour)
    print("==================================================")

    # Run the simulation
    info_dict, output_dict = run_taxi_simulation(test_path, graph_file_path, algorithm, objective, solution_mode,
                                                 time_window_min, nb_scenario, cust_node_hour, known_portion)

    # print solution
    result = {**info_dict, **output_dict}
    print_dict_as_table(result)


def match_enum(arg, enum):
    enum_values = {e.value.lower(): e for e in enum}
    match = difflib.get_close_matches(arg.lower(), enum_values.keys(), n=1, cutoff=.2)
    if match:
        return enum_values[match[0]]

    raise ValueError("Not found in enum: " + arg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a taxi simulation',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--instance", type=str, default="Med_1",
                        help="folder of the instance to test. Default: Med_1")
    parser.add_argument("-o", "--objective", type=str, default="total_customers",
                        help="The optimization objective to achieve:\n"
                             "- total_Profit: total profit of served requests.\n"
                             "- waiting_time: total wait time of served requests.\n"
                             "- total_customers: total number of served customers.\n"
                             "Default: total_customers")
    parser.add_argument("-tw", "--time-window", type=int, default=3,
                        help="Size of the time window in minutes to serve a request. Default: 3")
    parser.add_argument("-m", "--sol-mode", type=str, default="offline",
                        help="The mode of solution:\n"
                             "- offline : all the requests revealed at the start (release time = 0 for all requests).\n"
                             "- fully_online : release time is equal to the ready time for all requests.\n"
                             "- online : requests are known 30 minutes before the ready time.\n"
                             "- partial : a portion of requests are known in adavnce.\n"
                             "Default: offline")
    parser.add_argument("-a", "--algorithm", type=str, default="mip_solver",
                        help="Algorithm used to optimize the plan:\n"
                             "- mip_solver : using the Gurobi MIP solver to solve the problem\n"
                             "- greedy : greedy approach to assign requests to vehicles.\n"
                             "- random : random approach to assign requests to vehicles.\n"
                             "- ranking : ranking approach to assign requests to vehicles.\n"
                             "- qualitative_consensus : consensus approach to assign requests to vehicles."
                                "(count solutions)\n"
                             "- quantitative_consensus : consensus approach to assign requests to vehicles."
                                "(credit the solutions based o total objective)\n"
                             "Default: mip_solver.")
    parser.add_argument("-ns", "--nb-scenario", type=int, default=20,
                        help="Total number of scenarios to be solved for consensus :\n")
    parser.add_argument("-cr", "--cust-rate", type=float, default=0.21,
                        help="The average rate of customers per node per hour :\n")
    parser.add_argument("-kp", "--known-portion", type=float, default=0,
                        help="portion of requests that are known in advance :\n")

    args = parser.parse_args()

    sol_mode = match_enum(args.sol_mode, SolutionMode)
    obj = match_enum(args.objective, Objectives)
    algorithm = match_enum(args.algorithm, Algorithm)

    run_example(args.instance, obj, args.time_window, algorithm, sol_mode,args.cust_rate, args.nb_scenario,
                args.known_portion)

