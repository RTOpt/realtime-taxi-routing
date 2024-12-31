import math
from typing import Any, Dict, List

from src.utilities.enums import Objectives
from src.utilities.tools import get_costs, get_durations
from src.utilities.config import SimulationConfig


class Solver:
    """
    A class to solve the taxi routing problem using a Mixed Integer Programming (MIP) approach with Gurobi.

        Attributes:
        ------------
        vehicle_request_assign: dictionary
            a dictionary for each vehicle to keep track of various attributes associated with each vehicle
            This dictionary allows for saving the assignments of trips to vehicles which is used to create
            the route plan
        network: Any
            The road network, including nodes representing stop points.
        duration : dictionary
            travel time matrix between possible stop points
        costs: dictionary
            driving costs
        algorithm: Algorithm(Enum)
            The optimization algorithm utilized for planning and assigning trips to vehicles.
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan (e.g., maximizing profit or minimizing wait time).
        objective_value: float
            The objective value from served requests.

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
                 simulation_config: SimulationConfig) -> None:
        """
        Input:
        ------------
        network: The transport network over which the dispatching occurs.
        vehicles: Set of input vehicles
        simulation_config : Configuration object containing all simulation parameters.
        """
        self.network = network
        self.algorithm = simulation_config.algorithm
        self.objective = simulation_config.objective
        self.objective_value = 0
        self.durations = get_durations(network)
        self.costs = get_costs(network)
        self.vehicle_request_assign: Dict[int, Dict[str, Any]] = {}

        for vehicle in vehicles:
            self.vehicle_request_assign[vehicle.id] = {
                'vehicle': vehicle,
                'assigned_requests': [],    # List of assigned requests
                'departure_stop': None,     # last stop point of the previous iteration (current route plan)
                'departure_time': 0,        # departure time from the departure_stop
                'last_stop': None,          # last stop point assigned to the vehicle on the current solution
                'last_stop_time': 0,        # departure time from the stop in the current solution
                'assign_possible': False,   # determine the possibility of assigning a trip to the vehicle
            }

        self.X: Dict[int, Dict[int, bool]] = {}  # Decision variables for trip connections between customers
        self.Y: Dict[int, Dict[int, bool]] = {}  # Decision variables for assigning customers to vehicles
        self.Z: Dict[int, bool] = {}  # Decision variables for whether a customer is served
        self.U: Dict[int, float] = {}  # Decision variables for departure times from customer locations


    def update_vehicle_state(self, selected_routes, current_time):
        """
            Function: Update departure time and point for the vehicles based on the current routes
            Input:
            ------------
                selected_routes : current vehicle routes
                current_time : current time of the simultaion
        """
        for route in selected_routes:
            vehicle_id = route.vehicle.id
            vehicle_info = self.vehicle_request_assign.get(vehicle_id, {})
            vehicle_info['assigned_requests'] = []

            if not route.next_stops:
                # vehicle route is empty
                last_stop = route.previous_stops[-1] if route.current_stop is None else route.current_stop
                departure_time = last_stop.departure_time if last_stop.departure_time != math.inf else last_stop.arrival_time
                if departure_time < current_time:
                    departure_time = current_time
                vehicle_info.update({
                    'departure_time': departure_time,
                    'departure_stop': last_stop.location.label,
                    'last_stop_time': departure_time,
                    'last_stop': last_stop.location.label,
                })
            else:
                last_stop = route.next_stops[-1]
                vehicle_info.update({
                    'departure_time': last_stop.arrival_time,
                    'departure_stop': last_stop.location.label,
                    'last_stop_time': last_stop.arrival_time,
                    'last_stop': last_stop.location.label,
                })

            self.vehicle_request_assign[vehicle_id] = vehicle_info

    def print_vehicle_request_assign(self) -> None:
        """
        Function: Prints the current state of the vehicle_request_assign dictionary.
        """
        for vehicle_id, data in self.vehicle_request_assign.items():
            assigned_request_ids = [request.id for request in data['assigned_requests']]
            if assigned_request_ids:
                print(f"  vehicle ID: {vehicle_id}")
                print(f"  Assigned Requests (IDs): {assigned_request_ids}")
                for key, value in data.items():
                    if key not in ['assigned_requests', 'vehicle']:
                        print(f"  {key}: {value}")
                print()

    def calc_reach_time(self, vehicle_info: Dict, trip: Any) -> float:
        """
        Function: Calculate the time a vehicle can reach the trip's origin.
        """

        reach_time = (vehicle_info['last_stop_time'] + self.durations[vehicle_info['last_stop']][trip.origin.label])
        return max(reach_time, trip.ready_time)

    def assign_trip_to_vehicle(self, vehicle_info: Dict, trip: Any):
        """
        Function: Assign trip to a vehicle

            Input:
            ------------
                trip : request to be assigned
                vehicle_info : dictionary of the selected vehicle to assign the request
            """
        vehicle_info['assigned_requests'].append(trip)
        reach_time_to_pickup = self.calc_reach_time(vehicle_info, trip)
        vehicle_info['last_stop_time'] = reach_time_to_pickup + trip.shortest_travel_time
        vehicle_info['last_stop'] = trip.destination.label

    def variables_declaration(self, K, P):
        """
        Declares variables for online solvers.

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        """
        # initialized with False
        self.X = {i.id: {j.id: False for j in P} for i in P}
        self.Y = {k.id: {i.id: False for i in P} for k in K}
        self.U = {i.id: 0.0 for i in P}
        self.Z = {i.id: False for i in P}

    def create_online_solution(self):
        """
        Function: determine the value of the variables in the model based on vehicle_request_assign dictionary
                the function is used to check the feasibility of the solution
        """
        for veh_id, veh_info in self.vehicle_request_assign.items():
            if len(veh_info['assigned_requests']) != 0:
                trip = veh_info['assigned_requests'][0]
                self.Y[veh_id][trip.id] = True
                self.U[trip.id] = max(trip.ready_time, (
                        veh_info['departure_time'] + self.durations[veh_info['departure_stop']][trip.origin.label]))
                self.Z[trip.id] = True

                for i in range(1, len(veh_info['assigned_requests'])):
                    prev_trip = veh_info['assigned_requests'][i - 1]
                    curr_trip = veh_info['assigned_requests'][i]
                    self.X[prev_trip.id][curr_trip.id] = True
                    self.U[curr_trip.id] = max(
                        curr_trip.ready_time,
                        self.U[prev_trip.id] + prev_trip.shortest_travel_time + self.durations[prev_trip.destination.label][
                            curr_trip.origin.label],
                    )
                    self.Z[curr_trip.id] = True

    def verify_constraints(self, K: List[Any], P: List[Any]) -> bool:
        """
        Verifies all constraints.

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if all constraints are satisfied, False otherwise.
        """
        return (
                self._verify_const_1(K, P) and
                self._verify_const_2(P) and
                self._verify_const_3(K, P) and
                self._verify_const_4(P) and
                self._verify_const_5(P) and
                self._verify_const_6(K, P)
        )

    def _verify_const_1(self, K: List[Any], P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (1)

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 1 is satisfied, False otherwise.
        """
        verified = True
        for f_i in P:
            sum_x = 0
            sum_y = 0
            for f_j in P:
                sum_x += (1 if self.X[f_j.id][f_i.id] else 0)

            for f_k in K:
                sum_y += (1 if self.Y[f_k.id][f_i.id] else 0)

            z_i = 1 if self.Z[f_i.id] else 0
            if z_i != sum_x + sum_y:
                verified = False
                break
        return verified

    def _verify_const_2(self, P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (2)

        Parameters:
        ------------
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 2 is satisfied, False otherwise.
        """
        verified = True
        for f_i in P:
            sum_x = 0
            for f_j in P:
                sum_x += (1 if self.X[f_i.id][f_j.id] else 0)

            z_i = 1 if self.Z[f_i.id] else 0
            if z_i < sum_x:
                verified = False
                break
        return verified

    def _verify_const_3(self, K: List[Any], P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (3)

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 3 is satisfied, False otherwise.
        """
        verified = True
        for f_k in K:
            sum_y = 0
            for f_i in P:
                sum_y += (1 if self.Y[f_k.id][f_i.id] else 0)

            if sum_y > 1:
                verified = False
                break
        return verified

    def _verify_const_4(self, P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (4)

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 4 is satisfied, False otherwise.
        """
        verified = True
        for f_i in P:
            ready_time_f_i = f_i.ready_time
            latest_time_f_i = f_i.latest_pickup
            if self.U[f_i.id] < ready_time_f_i or self.U[f_i.id] > latest_time_f_i:
                verified = False
                break
        return verified

    def _verify_const_5(self, P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (5)

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 5 is satisfied, False otherwise.
        """
        verified = True
        for f_i in P:
            for f_j in P:
                if f_i != f_j:
                    T_ij = f_i.shortest_travel_time + self.durations[f_i.destination.label][f_j.origin.label]
                    if (self.U[f_j.id] - self.U[f_i.id]).__round__(3) < (
                            T_ij if self.X[f_i.id][f_j.id] else (f_j.ready_time - f_i.latest_pickup)).__round__(3):
                        verified = False
                        break
            if not verified:
                break
        return verified

    def _verify_const_6(self, K: List[Any], P: List[Any]) -> bool:
        """
        Function to verify the validation of the Constraint (6)

        Parameters:
        ------------
        K: List of vehicles.
        P: List of customers to serve.

        Returns:
        --------
        bool: True if Constraint 6 is satisfied, False otherwise.
        """
        verified = True
        for f_i in P:
            for f_k in K:
                T_ki = self.durations[self.vehicle_request_assign[f_k.id]['departure_stop']][f_i.origin.label]
                if self.U[f_i.id].__round__(3) < ((self.vehicle_request_assign[f_k.id]['departure_time'] + T_ki) if
                self.Y[f_k.id][f_i.id] else f_i.ready_time).__round__(3):
                    verified = False
                    break
            if not verified:
                break
        return verified


    def calc_objective_value(self, K, P):
        """
        Function to calculate the objective value
            Input:
            ------------
            K : set of vehicles
            P : set of customers to serve

            Hint:
                - you can use self.vehicle_request_assign dictionary for information about the vehicles
                - you can use self.costs or self.durations for cost and time matrix if required

        """
        value = 0
        if self.objective == Objectives.TOTAL_CUSTOMERS:
            value = sum(1 for f_i in P if self.Z[f_i.id])

        elif self.objective == Objectives.TOTAL_PROFIT:
            """you should write your code here ..."""
        elif self.objective == Objectives.WAIT_TIME:
            """you should write your code here ..."""

        self.objective_value = value


