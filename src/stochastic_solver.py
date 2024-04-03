from src.Offline_solver import (create_model, define_objective_total_customers, define_objective_total_wait_time,
                                define_objective_total_profit, define_objective)
from src.utilities import Objectives, Algorithm
from src.constraints_and_objectives import verify_all_constraints
from src.solver import Solver
from src.test_generator import create_random_requests


class StochasticSolver(Solver):
    """Provide online stochastic solution to optimize the vehicle routing and the trip-route assignment. This
        method includes:
            1. qualitative_consensus
            2. quantitative_consensus

        Attributes
        ------------
        nb_scenario: int
            Total number of scenarios that are possible to solve at each time
        cust_node_hour: float
            the average rate of customers per node (in the network) per hour
            - for small size tests select 0.2
            - for medium size tests select 0.3
            - for large size tests select 0.7

        Attributes from the parent class:
        ------------
        vehicle_request_assign: dictionary
            a dictionary for each vehicle to keep track of various attributes associated with each vehicle
            This dictionary allows for saving the assignments of trips to vehicles which is used to create
            the route plan
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

    def __init__(self, network, algorithm, objective, vehicles, nb_scenario, cust_node_hour):
        super().__init__(network, algorithm, objective, vehicles)
        self.__nb_scenario = nb_scenario
        self.__cust_node_hour = cust_node_hour

    @property
    def cust_node_hour(self):
        """Getter for cust_node_hour."""
        return self.__cust_node_hour

    @property
    def nb_scenario(self):
        """Getter for nb_scenario."""
        return self.__nb_scenario

    def stochastic_solver(self, K, P_not_assigned, Y, X, Z, U, G, current_time):
        """ Function: find a solution to assign ride requests to vehicles after arrival
            Input:
            ------------
                K : set of vehicles
                P_not_assigned : set of customers that are not assigned to be served
                X , Y, U, Z : Model variables
                G : The road network, including nodes representing stop points.
                current_time: current time of the system which is used to generate scenarios

        """

        # Step 1: assign requests to the vehicles/ routes
        P_not_assigned = sorted(P_not_assigned, key=lambda x: x.ready_time)
        time_window = (P_not_assigned[0].latest_pickup - P_not_assigned[0].ready_time) / 60
        if self.algorithm == Algorithm.QUANTITATIVE_CONSENSUS:
            assigned_requests = self.quantitative_consensus(P_not_assigned, G, K, time_window, current_time)
        elif self.algorithm == Algorithm.QUALITATIVE_CONSENSUS:
            assigned_requests = self.qualitative_consensus(P_not_assigned, G, K, time_window, current_time)

        # Step 2: check the feasibility of then solution
        self.create_online_solution(X, Y, U, Z)
        if verify_all_constraints(X, Y, U, Z, K, assigned_requests, self.vehicle_request_assign, self.durations):
            self.calc_objective_value(X, Y, U, Z, K, P_not_assigned)
            self.total_customers_served = sum(1 for f_i in P_not_assigned if Z[f_i.id])

        else:
            raise ValueError("The solution is not feasible")

    def qualitative_consensus(self, P_not_assigned, G, K, time_window, current_time):
        """ Function: find a solution based on consensus method to assign ride requests to vehicles after arrival.


            Input:
            ------------
                G : The road network, including nodes representing stop points.
                P_not_assigned : set of customers that are not assigned to be served
                K : set of vehicles
                time_window: size of the time window in minutes to serve a request
                    it is used to generate scenarios
                current_time: current time of the system which is used to generate scenarios

            Output:
            ------------
                assigned_requests: List of assigned requests

            Hint:
                - you should use create_random_requests function in the test_generator.py to generate scenarios
                - use functions in Offline_solver.py to solve the problem for each scenario
                - assign one request at a time to vehicles
                - you should count the number of times a request is assigned to a vehicle

        """
        assigned_requests = []
        """you should write your code here ..."""

        return assigned_requests

    def quantitative_consensus(self, P_not_assigned, G, K, time_window, current_time):
        """ Function: find a solution based on consensus method to assign ride requests to vehicles after arrival.


            Input:
            ------------
                G : The road network, including nodes representing stop points.
                P_not_assigned : set of customers that are not assigned to be served
                K : set of vehicles
                time_window: size of the time window in minutes to serve a request
                    it is used to generate scenarios
                current_time: current time of the system which is used to generate scenarios

            Output:
            ------------
                assigned_requests: List of assigned requests

            Hint:
                - you should use create_random_requests function in the test_generator.py to generate scenarios
                - use functions in Offline_solver.py to solve the problem for each scenario
                - assign one request at a time to vehicles
                - you should credit the value of optimal solution for a request that is assigned to a vehicle

        """
        assigned_requests = []
        """you should write your code here ..."""

        return assigned_requests

    def calc_objective_value(self, X, Y, U, Z, K, P):
        """ Function to calculate the objective value
            Input:
            ------------
            K : set of vehicles
            P : set of customers to serve
            X, Y , U, Z : Model variables

            Hint:
                - copy the same code you used in online_solver.py
        """
        value = 0
        if self.objective == Objectives.TOTAL_CUSTOMERS:
            value = sum(1 for f_i in P if Z[f_i.id])

        elif self.objective == Objectives.PROFIT:
            """you should write your code here ..."""

        elif self.objective == Objectives.WAIT_TIME:
            """you should write your code here ..."""

        self.objective_value = value
