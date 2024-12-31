import random
from typing import Any, List
import logging

from src.utilities.config import SimulationConfig
from src.utilities.enums import Algorithm, Objectives
from src.solvers.solver import Solver

logger = logging.getLogger(__name__)


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

        durations : dictionary
            travel time matrix between possible stop points
            example: for duration between destination of trip_i and the origin of trip_j use:
                     self.durations[trip_i.destination.label][trip_i.origin.label]

        costs: dictionary
            driving costs (it works based on location ids like durations)
        algorithm: Algorithm(Enum)
            The optimization algorithm utilized for planning and assigning trips to vehicles.
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan (e.g., maximizing profit or minimizing wait time).
        objective_value: float
            The objective value from served requests.
        total_customers_served: int
            The count of customers successfully served.

        X: Dict[int, Dict[int, bool]]
            Binary variables indicating if customer i is picked immediately after j by a taxi.
        Y: Dict[int, Dict[int, bool]]
            Binary variables indicating if customer i is picked up by vehicle k as the first customer.
        U: Dict[int, float]
            Pickup times for customers.
        Z: Dict[int, bool]
            Binary variables indicating if customer i is selected to be served.
    """

    def __init__(self,
                 network: Any,
                 vehicles: List[Any],
                 simulation_config: SimulationConfig):
        super().__init__(network, vehicles, simulation_config)
        # Assign random numbers to each vehicle request assignment
        for veh_id, temp_dict in self.vehicle_request_assign.items():
            temp_dict['random_number'] = random.random()

    def determine_available_vehicles(self, trip):
        """ Function: determine the possibility of assigning a trip to vehicles
            Input:
            ------------
                trip : ride request to serve
            Hint:
                - you can use self.vehicle_request_assign dictionary for information about the vehicles
                - you can use functions from the parent class (Solver)

        """
        """you should write your code here ..."""


    def online_solver(self, K, P_not_assigned, rejected_trips):
        """
        Function: find a solution to assign ride requests to vehicles after arrival

            Input:
            ------------
                K : set of vehicles
                P_not_assigned : set of customers that are not assigned to be served
                rejected_trips: List of trips that are rejected in the optimization process.

            steps:
            1. assign requests to the vehicles/ routes based on the chosen algorithm
            2. check the feasibility of then solution
        """

        # Step 1: assign requests to the vehicles/ routes
        sorted_requests = sorted(P_not_assigned, key=lambda x: x.ready_time)

        if self.algorithm == Algorithm.GREEDY:
            assigned_requests = self.greedy_assign(sorted_requests, rejected_trips)
        elif self.algorithm == Algorithm.RANDOM:
            assigned_requests = self.random_assign(sorted_requests, rejected_trips)
        elif self.algorithm == Algorithm.RANKING:
            assigned_requests = self.ranking_assign(sorted_requests, rejected_trips)
        else:
            logger.error("Unsupported algorithm: %s", self.algorithm)
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

        # Step 2: check the feasibility of then solution
        self.create_online_solution()
        if self.verify_constraints(K, assigned_requests):
            self.calc_objective_value(K, sorted_requests)
            self.total_customers_served = sum(1 for f_i in P_not_assigned if self.Z[f_i.id])
            logger.info("Online solver solution is feasible. Served %d customers.", self.total_customers_served)

        else:
            logger.error("The solution is not feasible.")
            raise ValueError("The solution is not feasible")

    def greedy_assign(self, P_not_assigned: List[Any], rejected_trips: List[Any]) -> List[Any]:
        """
        Function: find a solution based on greedy method to assign ride requests to vehicles after arrival

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
                  "determine_available_vehicles" function
                - If no vehicle is available for a task, add it to the rejected_trips list
                - if a vehicle is selected to assign a request:
                    - Use the assign_trip_to_vehicle function from Solver class to assign the task to the selected vehicle
                    - add trip to the list of assigned_requests

        """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your greedy algorithm here:
        """

        return assigned_requests

    def random_assign(self, P_not_assigned: List[Any], rejected_trips: List[Any]) -> List[Any]:
        """
        Function: find a solution based on random method to assign ride requests to vehicles after arrival

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
              "determine_available_vehicles" function
            - If no vehicle is available for a task, add it to the rejected_trips list
            - if a vehicle is selected to assign a request:
                - Use the assign_trip_to_vehicle function to assign the task to the selected vehicle
                - add trip the list of assigned_requests
        """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your random algorithm here:
        """

        return assigned_requests

    def ranking_assign(self, P_not_assigned: List[Any], rejected_trips: List[Any]) -> List[Any]:
        """
        Function: find a solution based on ranking method to assign ride requests to vehicles after arrival
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
              "determine_available_vehicles" function
            - If no vehicle is available for a task, add it to the rejected_trips list
            - if a vehicle is selected to assign a request:
                - Use the assign_trip_to_vehicle function to assign the task to the selected vehicle
                - add trip the list of assigned_requests

        """
        # for each request find the best insertion position
        assigned_requests = []
        """
            Implement your ranking algorithm here:
        """

        return assigned_requests
