from src.Offline_solver import create_model, solve_offline_model, define_objective
from src.utilities import DestroyMethod
from src.solver import Solver


def destroy_bonus(K, P, model, Y_var, X_var, Z_var, U_var):
    """ Function: An arbitrary destroy method

        Input:
        ------------
            K : set of vehicles
            P : set of customers to serve
            model: The Gurobi model to optimize.
            Y_var, X_var, Z_var, U_var: The Decision variables of the Gurobi model

        Note:
            - Include comments where necessary to explain your proposed function
            - you can use any of the inputs if required
    """
    """you should write your code here ..."""


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

    def __init__(self, network, algorithm, objective, vehicles, destroy_method):
        super().__init__(network, algorithm, objective, vehicles)
        self.__initial_solution = None
        self.__destroy_method = destroy_method

    @property
    def destroy_method(self):
        """Getter for destroy_method."""
        return self.__destroy_method

    @property
    def initial_solution(self):
        """Getter for cust_node_hour."""
        return self.__initial_solution

    def re_optimizer(self, K, P_not_served, rejected_trips):
        """ Function: Re-optimize the solution based on destroy and repair
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

        # create model
        model, Y_var, X_var, Z_var, U_var = create_model(K, P_not_served, self.durations,
                                                         self.vehicle_request_assign)

        if self.initial_solution is not None:
            if self.destroy_method == DestroyMethod.FIX_ARRIVALS:
                # destroy by fixing a time window around the arrival times in the initial solution
                self.destroy_fix_arrival_times(P_not_served, U_var)

            elif self.destroy_method == DestroyMethod.FIX_VARIABLES:
                # destroy by fixing some of the variables based on the initial solution
                self.destroy_fix_variables(K, P_not_served, Y_var, X_var)
            elif self.destroy_method == DestroyMethod.BONUS:
                # destroy the solution by your suggested function
                destroy_bonus(K, P_not_served, model, Y_var, X_var, Z_var, U_var)

        # add objective
        define_objective(self.objective, X_var, Y_var, U_var, Z_var, model, K, P_not_served, self.costs,
                         self.vehicle_request_assign)

        # solve and get solution
        obj_value = solve_offline_model(model, P_not_served, K, Y_var, X_var, Z_var,
                                        rejected_trips, self.vehicle_request_assign)

        self.save_solution(Y_var, X_var, Z_var, U_var)

    def save_solution(self, Y_var, X_var, Z_var, U_var):
        """ Function: save the solution

            Input:
            ------------
                Y_var, X_var, Z_var, U_var : The Decision variables of the Gurobi model

        """
        # Extracting values of decision variables
        Y = {key[0]: {key[1]: var.X for key, var in Y_var.items() if key[0] == key[1]} for key in Y_var}
        X = {key[0]: {key[1]: var.X for key, var in X_var.items() if key[0] == key[1]} for key in X_var}
        Z = {key: var.X for key, var in Z_var.items()}
        U = {key: var.X for key, var in U_var.items()}

        assignment_dict = {}
        for vehicle_id, assignment_info in self.vehicle_request_assign.items():
            assignment_dict[vehicle_id] = {'assigned_requests': assignment_info['assigned_requests']}

        self.__initial_solution = {
            'X': X,
            'Y': Y,
            'U': U,
            'Z': Z,
            'assignment_dict': assignment_dict
        }

    def destroy_fix_arrival_times(self, P, U_var):
        """ Function: For each request in the initial solution, this function fixes its arrival time within
            a time window of 2 min

            Input:
            ------------
                P : set of customers to serve
                Y_var, X_var, Z_var, U_var: The Decision variables of the Gurobi model
        """
        """you should write your code here ..."""

    def destroy_fix_variables(self, K, P, Y_var, X_var):
        """ Function: Fix some of Y_var, X_var variables based on the initial solution

            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                Y_var, X_var: The Decision variables of the Gurobi model

            Note:
                - Forbid the arcs that goes from one request to another one that were in different vehicle
                - Forbid the arcs that goes from departing node of a vehicle to other requests that were in different
                  vehicle
        """
        """you should write your code here ..."""

    def destroy_bonus(self, K, P, model, Y_var, X_var, Z_var, U_var):
        """ Function: An arbitrary destroy method

            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                model: The Gurobi model to optimize.
                Y_var, X_var, Z_var, U_var: The Decision variables of the Gurobi model

            Note:
                - Include comments where necessary to explain your proposed function
                - you can use any of the inputs if required
        """
        """you should write your code here ..."""
