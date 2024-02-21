import copy
import random

from src.utilities import Algorithm, Objectives
from src.constraints_and_objectives import verify_all_constraints
from src.solver import Solver


class OnlineSolver(Solver):
    """Provide online solution to optimize the vehicle routing and the trip-route assignment. This
        method includes:
            1. greedy solver
            2. random solver
            3. ranking solver

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

    def __init__(self, network, algorithm, objective, vehicles):
        super().__init__(network, algorithm, objective, vehicles)


    def determine_available_vehicles(self, trip):
        """ Function: determine the possibility of assigning a trip to vehicles
            Input:
            ------------
                trip : ride request to serve
            Hint:
                you can use "vehicle_request_assign" and "durations" attributes of the class

        """
        """you should write your code here ..."""

    def assign_trip_to_vehicle(self, selected_vehicle_info, trip):
        """ Function: assign trip to a vehicle
            Input:
            ------------
                trip : request to be assigned
                selected_vehicle_info : dictionary of the selected vehicle to assign the request
            """
        selected_vehicle_info['assigned_requests'].append(trip)
        reach_time_to_pick = self.calc_reach_time(selected_vehicle_info, trip)

        selected_vehicle_info['last_stop_time'] = reach_time_to_pick + trip.shortest_travel_time
        selected_vehicle_info['last_stop'] = trip.destination.label

    def calc_objective_value(self, X, Y, U, Z, K, P):
        """ Function to calculate the objective value
            Input:
            ------------
            K : set of vehicles
            P : set of customers to serve
            X, Y , U, Z : Model variables

            Hint:
                you can
        """
        value = 0
        if self.objective == Objectives.TOTAL_CUSTOMERS:
            value = sum(1 for f_i in P if Z[f_i.id])

        elif self.objective == Objectives.PROFIT:
            """you should write your code here ..."""

        elif self.objective == Objectives.WAIT_TIME:
            """you should write your code here ..."""

        self.objective_value = value

    def online_solver(self, K, P_not_assigned, Y, X, Z, U, rejected_trips):
        """ Function: find a solution to assign ride requests to vehicles after arrival
            Input:
            ------------
                K : set of vehicles
                P_not_assigned : set of customers that are not assigned to be served
                X , Y, U, Z : Model variables
                rejected_trips: List of trips that are rejected in the optimization process.

            Output:
            ------------
                obj_value: The objective value of the optimized model

            steps:
            1. assign requests to the vehicles/ routes based on the chosen algorithm
            2. check the feasibility of then solution
        """

        # Step 1: assign requests to the vehicles/ routes
        sorted_requests = sorted(P_not_assigned, key=lambda x: x.ready_time)

        if self.algorithm == Algorithm.GREEDY:
            assigned_requests = self.greedy_assign(sorted_requests, rejected_trips)
        elif self.algorithm == Algorithm.RANDOM:
            assigned_requests = self.ranking_assign(sorted_requests, rejected_trips)
        elif self.algorithm == Algorithm.RANKING:
            assigned_requests = self.ranking_assign(sorted_requests, rejected_trips)

        # Step 2: check the feasibility of then solution
        self.create_online_solution(X, Y, U, Z)
        if verify_all_constraints(X, Y, U, Z, K, assigned_requests, self.vehicle_request_assign, self.durations):
            self.calc_objective_value(X, Y, U, Z, K, sorted_requests)
            self.total_customers_served = sum(1 for f_i in P_not_assigned if Z[f_i.id])

        else:
            raise ValueError("The solution is not feasible")

    def greedy_assign(self, P_not_assigned, rejected_trips):
        """ Function: find a solution based on greedy method to assign ride requests to vehicles after arrival
            Input:
            ------------
                P_not_assigned : set of customers that are not assigned to be serve
                rejected_trips: List of trips that are rejected in the optimization process.

            Output:
            ------------
                assigned_requests: List of assigned requests

            Hint:
                - for each trip in P_not_assigned you have to select a vehicle to assign or reject the request
                - evaluating the feasibility of assigning a trip to a vehicle should be done inside
                  "assign_trip_to_vehicle" function and setting ['assign_possible'] to True/False
                - If no vehicle is available for a task, add it to the rejected_trips list
                - Use the assign_trip_to_vehicle function to assign the task to the selected vehicle

        """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your greedy algorithm here:
        """

        return assigned_requests

    def random_assign(self, P_not_assigned, rejected_trips):
        """ Function: find a solution based on random method to assign ride requests to vehicles after arrival
        Input:
        ------------
            P_not_assigned : set of customers that are not assigned to be serve
            rejected_trips: List of trips that are rejected in the optimization process.

        Output:
        ------------
            assigned_requests: List of assigned requests

        Hint:
            - for each trip in P_not_assigned you have to select a vehicle to assign or reject the request
            - evaluating the feasibility of assigning a trip to a vehicle should be done inside
              "assign_trip_to_vehicle" function and setting ['assign_possible'] to True/False
            - If no vehicle is available for a task, add it to the rejected_trips list
            - Use the assign_trip_to_vehicle function to assign the task to the selected vehicle

    """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your random algorithm here:
        """

        return assigned_requests

    def ranking_assign(self, P_not_assigned, rejected_trips):
        """ Function: find a solution based on ranking method to assign ride requests to vehicles after arrival
        Input:
        ------------
            P_not_assigned : set of customers that are not assigned to be serve
            rejected_trips: List of trips that are rejected in the optimization process.

        Output:
        ------------
            assigned_requests: List of assigned requests

        Hint:
            - for each trip in P_not_assigned you have to select a vehicle to assign or reject the request
            - evaluating the feasibility of assigning a trip to a vehicle should be done inside
              "assign_trip_to_vehicle" function and setting ['assign_possible'] to True/False
            - If no vehicle is available for a task, add it to the rejected_trips list
            - Use the assign_trip_to_vehicle function to assign the task to the selected vehicle

    """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your ranking algorithm here:
        """

        return assigned_requests
