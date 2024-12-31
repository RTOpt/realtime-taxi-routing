from src.solvers.offline_solver import OfflineSolver
from src.utilities.enums import DestroyMethod
from src.solvers.solver import Solver
from src.utilities.config import SimulationConfig
from typing import Any, Dict, List



class ReOptimizer(Solver):
    """Provide methods to Re-optimize the vehicle routing and the trip-route assignment based on destroy and repair
    ideas. This class includes three destroy function ():
            1. destroy_fix_arrival_times
            2. destroy_fix_variables
            3. destroy_bonus

        Attributes
        ------------
        destroy_method: DestroyMethod(Enum)
            Method used for destruction in LNS algorithm

        initial_solution : dictionary
            contains initial values for decision variables.

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
    """

    def __init__(self,
                 network: Any,
                 vehicles: List[Any],
                 simulation_config: SimulationConfig) -> None:
        super().__init__(network, vehicles, simulation_config)
        self.initial_solution : Dict[str, Any] = {}
        self.destroy_method = simulation_config.algorithm_params["destroy_method"]


    def re_optimizer(self, K, P_not_served, rejected_trips):
        """
        Function: Re-optimize the solution based on destroy and repair
            Input:
            ------------
                K : set of vehicles
                P_not_served : set of customers that are not served yet
                rejected_trips: List of trips that are rejected in the optimization process.

            steps:
            1. create the mathematical model in Gurobi
            2. destroy (fix) a part of the current solution if it exists
            3. repair (re-optimize) the solution using mip solver
            4. save the final solution
        """

        # Create and configure the offline model
        offline_model = OfflineSolver(self.network, self.objective)
        offline_model.create_model(K, P_not_served, self.vehicle_request_assign)

        if self.initial_solution:
            if self.destroy_method == DestroyMethod.FIX_ARRIVALS:
                # destroy by fixing a time window around the arrival times in the initial solution
                self.destroy_fix_arrival_times(P_not_served, offline_model)

            elif self.destroy_method == DestroyMethod.FIX_VARIABLES:
                # destroy by fixing some of the variables based on the initial solution
                self.destroy_fix_variables(K, P_not_served, offline_model)
            elif self.destroy_method == DestroyMethod.BONUS:
                # destroy the solution by your suggested function
                self.destroy_bonus(K, P_not_served, offline_model)

        # add objective
        offline_model.define_objective(K, P_not_served, self.vehicle_request_assign)

        # solve and get solution
        offline_model.solve()
        offline_model.extract_solution(K, P_not_served, rejected_trips, self.vehicle_request_assign)

        self.save_solution(offline_model)

    def save_solution(self, offline_model: OfflineSolver):
        """
        Function: Saves the solution from the offline model into the initial_solution attribute.

            Input:
            ------------
                offline_model: The Gurobi MIP model.

        """
        # Extracting values of decision variables
        self.Y: Dict[Any, Dict[Any, float]] = {
            key[0]: {sub_key[1]: var.X for sub_key, var in offline_model.Y_var.items() if sub_key[0] == key[0]}
            for key in offline_model.Y_var.keys()
        }
        self.X: Dict[Any, Dict[Any, float]] = {
            key[0]: {sub_key[1]: var.X for sub_key, var in offline_model.X_var.items() if sub_key[0] == key[0]}
            for key in offline_model.X_var.keys()
        }
        self.Z: Dict[Any, float] = {key: var.X for key, var in offline_model.Z_var.items()}
        self.U: Dict[Any, float] = {key: var.X for key, var in offline_model.U_var.items()}

        assignment_dict: Dict[Any, Dict[str, List[Any]]] = {
            vehicle_id: {
                'assigned_requests': assignment_info['assigned_requests']
            }
            for vehicle_id, assignment_info in self.vehicle_request_assign.items()
        }

        self.initial_solution = {
            'X': self.X,
            'Y': self.Y,
            'U': self.U,
            'Z': self.Z,
            'assignment_dict': assignment_dict
        }

    def destroy_fix_arrival_times(self, P, offline_model: OfflineSolver) -> None:
        """
        Function: For each request in the initial solution, this function fixes its arrival time within
            a time window of 2 min

            Input:
            ------------
                P : set of customers to serve
                offline_model: The Gurobi MIP model.
        """
        """you should write your code here ..."""

    def destroy_fix_variables(self, K, P, offline_model: OfflineSolver):
        """
        Function: Fix some of Y_var, X_var variables based on the initial solution

            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                offline_model: The Gurobi model to optimize.

            Note:
                - Forbid the arcs that goes from one request to another one that were in different vehicle
                - Forbid the arcs that goes from departing node of a vehicle to other requests that were in different
                  vehicle
        """
        """you should write your code here ..."""


    def destroy_bonus(self, K, P, offline_model: OfflineSolver):
        """ Function: An arbitrary destroy method

            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                offline_model: The Gurobi model to optimize.

            Note:
                - Include comments where necessary to explain your proposed function
                - you can use any of the inputs if required
        """
        """you should write your code here ..."""

