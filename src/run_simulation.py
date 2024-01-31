import os
from multimodalsim.__main__ import extract_simulation_output
from multimodalsim.simulator.simulation import Simulation
from multimodalsim.optimization.optimization import Optimization
from src.taxi_dispatcher import TaxiDispatcher
from multimodalsim.observer.environment_observer import StandardEnvironmentObserver
from src.data_reader import TaxiDataReader
import src.utilities as ut


def run_taxi_simulation(test_folder, graph_file_path, algorithm, objective, solution_mode, time_window):
    """ Function: Conducts a simulation of taxi dispatching, based on specified parameters.
        Input:
        ------------
        test_folder : str
            The directory path where the test files are located.
        graph_file_path : str
            The file path to the transportation network graph.
        algorithm : Algorithm(Enum)
            The optimization algorithm to use for routing and assignment.
        objective : Objectives(Enum)
            The optimization objective to achieve (e.g., profit maximization).
                - total_Profit: total profit of served requests
                - waiting_time: total wait time of served requests
                - total_customers: total number of served customers
        solution_mode : SolutionMode(Enum)
            The mode of solution,
                - offline : all the requests revealed at the start (release time = 0 for all requests)
                - fully_online : release time is equal to the ready time for all requests
                - online : requests are known 30 minutes before the ready time
        time_window : int
            Time window for picking up the requests

        Output:
        ------------
        len(trips): number of trips
        len(vehicles): number of vehicles
        output_dict: a dictionary of output metrics.
    """
    # Run the simulation
    trips_count, vehicles_count, output_dict = run_simulation(test_folder, graph_file_path, algorithm,
                                                              objective, solution_mode, time_window)
    # Compile information about the test and results
    info_dict = {
        'Test': test_folder,
        '# Trips': trips_count,
        '# Vehicles': vehicles_count,
        'Time window (min)': time_window,
        'Solution Mode': solution_mode.value,
    }

    return info_dict, output_dict


def run_simulation(test_folder, graph_file_path, algorithm, objective, solution_mode, time_window):
    """ Function: Conducts a simulation of taxi dispatching, based on specified parameters.
        Input:
        ------------
        test_folder : str
            The directory path where the test files are located.
        graph_file_path : str
            The file path to the transportation network graph.
        algorithm : Algorithm(Enum)
            The optimization algorithm to use for routing and assignment.
        objective : Objectives(Enum)
            The optimization objective to achieve (e.g., profit maximization).
                - total_Profit: total profit of served requests
                - waiting_time: total wait time of served requests
                - total_customers: total number of served customers
        solution_mode : SolutionMode(Enum)
            The mode of solution,
                - offline : all the requests revealed at the start (release time = 0 for all requests)
                - fully_online : release time is equal to the ready time for all requests
                - online : requests are known 30 minutes before the ready time
        time_window : int
            Time window for picking up the requests

        Output:
        ------------
        len(trips): number of trips
        len(vehicles): number of vehicles
        output_dict: a dictionary of output metrics.
    """
    # Define file paths for requests, vehicles, and output directory
    requests_file_path = f"{test_folder}/customers.json"
    vehicles_file_path = f"{test_folder}/taxis.json"
    output_file_path = os.path.join(test_folder, "output/")

    # Ensure output directory exists
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)

    # Read and prepare data
    data_reader = TaxiDataReader(requests_file_path, vehicles_file_path, graph_file_path, vehicles_end_time=100000)
    network_graph = data_reader.get_json_graph()
    ut.draw_network(network_graph, graph_file_path)
    vehicles, routes_by_vehicle_id = data_reader.get_json_vehicles()
    trips = data_reader.get_json_trips(solution_mode, time_window)

    # Initialize simulation components
    dispatcher = TaxiDispatcher(network_graph, algorithm, objective)
    opt = Optimization(dispatcher)
    environment_observer = StandardEnvironmentObserver()

    # Initialize and run the simulation
    simulation = Simulation(opt, trips, vehicles, routes_by_vehicle_id, network=network_graph,
                            environment_observer=environment_observer)
    simulation.simulate()

    # Extract and process simulation output
    extract_simulation_output(simulation, output_file_path)
    output_dict = dispatcher.extract_output()

    # Return relevant data
    return len(trips), len(vehicles), output_dict