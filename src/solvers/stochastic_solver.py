from src.solvers.offline_solver import OfflineSolver
from src.solvers.solver import Solver
from src.utilities.enums import ConsensusParams
from src.utilities.create_scenario import create_random_requests
from typing import Any, Dict, List
from src.utilities.config import SimulationConfig



class StochasticSolver(Solver):
    """
    Provide online stochastic solution to optimize the vehicle routing and the trip-route assignment.
    It uses scenario generation and then solves each scenario with an offline solver.
    Two type of consensus algorithm are defined:
        - qualitative: Increment a counter for the best request in each scenario.
        - quantitative: Credit the best request with the optimal solution value.

        Attributes
        ------------
        consensus_type: ConsensusParams(Enum)
            The type of consensus algorithm
        nb_scenario: int
                Total number of scenarios that are possible to solve at each time
        scenario_param: Dict[str, Any]
            parameters used in generating scenarios

        Attributes from the parent class:
        ------------
        a dictionary for each vehicle to keep track of various attributes associated with each vehicle
            This dictionary allows for saving the assignments of trips to vehicles which is used to create
            the route plan. it keeps the following data:

                - vehicle: The vehicle object representing the specific vehicle in consideration.
                - assigned_requests: A list containing the requests assigned to the vehicle.
                - departure_stop: The last stop point of the vehicle in the previous iteration,
                    which serves as the starting point for the current route plan.
                - departure_time: The departure time from the departure stop point. This indicates
                    when the vehicle is scheduled to depart from its starting point.
                - last_stop: The last stop point assigned to the vehicle in the current solution.
                - last_stop_time: The departure time from the last assigned stop in the current solution.
                - assign_possible: A boolean value indicating whether it is possible to assign a trip to the vehicle.
                    (This value may be updated dynamically within the "determine_available_vehicles" function.
                    However, using this value is optional!)

        network: Any
            The road network, including nodes representing stop points.
        durations : dictionary
            travel time matrix between possible stop points
        costs: dictionary
            driving costs
        algorithm: Algorithm(Enum)
            The optimization algorithm utilized for planning and assigning trips to vehicles.
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan (e.g., maximizing profit or minimizing wait time).
        objective_value: float
            The objective value from served requests.
        total_customers_served: int
            The count of customers successfully served.
    """

    def __init__(self,
                 network: Any,
                 vehicles: List[Any],
                 simulation_config: SimulationConfig):
        super().__init__(network, vehicles, simulation_config)
        self.consensus_type = simulation_config.algorithm_params["consensus_param"]
        self.nb_scenario = simulation_config.algorithm_params["nb_scenario"]

        self.scenario_param = {
            'time_window': simulation_config.time_window,       # Time window for picking up the requests
            'cust_node_hour': simulation_config.algorithm_params["cust_node_hour"],  # the average rate of customers per node (in the network) per hour
            'known_portion': simulation_config.known_portion,    # percentage of requests that are known in advance
            'advance_notice': simulation_config.advance_notice,  # Fixed amount of time (in minutes) the requests are released before their ready time.
        }


    def stochastic_solver(self, K, P_not_assigned, current_time):
        """
        Function: find a solution to assign ride requests to vehicles after arrival
            Input:
            ------------
                K : set of vehicles
                P_not_assigned : set of customers that are not assigned to be served
                current_time: current time of the system which is used to generate scenarios
        """

        # Step 1: assign requests to the vehicles/ routes
        P_not_assigned = sorted(P_not_assigned, key=lambda x: x.ready_time)
        assigned_requests = []

        if self.consensus_type == ConsensusParams.QUANTITATIVE:
            assigned_requests = self.quantitative_consensus(K, P_not_assigned, current_time)

        elif self.consensus_type == ConsensusParams.QUALITATIVE:
            assigned_requests = self.qualitative_consensus(K, P_not_assigned, current_time)

        # Step 2: check the feasibility of then solution
        self.create_online_solution()
        if self.verify_constraints(K, assigned_requests):
            self.calc_objective_value(K, P_not_assigned)
            self.total_customers_served = sum(1 for f_i in P_not_assigned if self.Z[f_i.id])

        else:
            raise ValueError("The solution is not feasible")

    def qualitative_consensus(self, K, P_not_assigned, current_time):
        """
        Function: find a solution based on consensus method to assign ride requests to vehicles after arrival.

            Input:
            ------------
                P_not_assigned : set of customers that are not assigned to be served
                K : set of vehicles
                current_time: current time of the system which is used to generate scenarios

            Output:
            ------------
                assigned_requests: List of assigned requests

            Hint:
                - you should use create_random_requests function in the create_scenario.py to generate scenarios
                - use functions in offline_solver.py to solve the problem for each scenario
                - assign one request at a time to vehicles
                - you should count the number of times a request is assigned to a vehicle

        """
        assigned_requests = []
        """you should write your code here ..."""

        return assigned_requests


    def quantitative_consensus(self, K, P_not_assigned, current_time):
        """
        Function: find a solution based on consensus method to assign ride requests to vehicles after arrival.

            Input:
            ------------
                K : set of vehicles
                P_not_assigned : set of customers that are not assigned to be served
                current_time: current time of the system which is used to generate scenarios

            Output:
            ------------
                assigned_requests: List of assigned requests

            Hint:
                - you should use create_random_requests function in the create_scenario.py to generate scenarios
                - use functions in offline_solver.py to solve the problem for each scenario
                - assign one request at a time to vehicles
                - you should credit the value of optimal solution for a request that is assigned to a vehicle
        """
        assigned_requests = []
        """you should write your code here ..."""
        return assigned_requests

