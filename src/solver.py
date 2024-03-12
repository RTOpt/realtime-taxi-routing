import math

from src.utilities import Algorithm, Objectives, get_costs, get_durations, get_distances


class Solver():
    """Provide solution to optimize the vehicle routing and the trip-route assignment.
        Attributes:
        ------------
        vehicle_request_assign: dictionary
            a dictionary for each vehicle to keep track of various attributes associated with each vehicle
            This dictionary allows for saving the assignments of trips to vehicles which is used to create
            the route plan
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
        total_customers_served: int
            The count of customers successfully served.

        """

    def __init__(self, network, algorithm, objective, vehicles):
        self.__algorithm = algorithm
        self.__objective = objective
        self.__total_customers_served = 0
        self.__objective_value = 0
        self.__durations = get_durations(network)
        self.__costs = get_costs(network)
        self.__vehicle_request_assign = {}
        for veh in vehicles:
            temp_dict = {}
            temp_dict['vehicle'] = veh
            temp_dict['assigned_requests'] = []  # List of assigned requests
            temp_dict['departure_stop'] = None   # last stop point of the previous iteration (current route plan)
            temp_dict['departure_time'] = 0      # departure time from the departure_stop
            temp_dict['last_stop'] = None        # last stop point assigned to the vehicle on the current solution
            temp_dict['last_stop_time'] = 0      # departure time from the stop in the current solution
            temp_dict['assign_possible'] = False  # determine the possibility of assigning a trip to the vehicle

            self.__vehicle_request_assign[veh.id] = temp_dict

    def update_vehicle_state(self, selected_routes):
        """
            Function: set departure time and point for the vehicles based on the current routes
                Input:
                ------------
                    selected_routes : current vehicle routes

                """
        for route in selected_routes:
            vehicle_id = route.vehicle.id
            vehicle_info = self.vehicle_request_assign.get(vehicle_id, {})
            vehicle_info['assigned_requests'] = []

            if len(route.next_stops) == 0:
                # vehicle route is empty
                last_stop = route.previous_stops[-1] if route.current_stop is None else route.current_stop
                vehicle_info['departure_time'] = last_stop.departure_time
                vehicle_info['departure_stop'] = last_stop.location.label
                vehicle_info['last_stop_time'] = last_stop.departure_time
                vehicle_info['last_stop'] = last_stop.location.label
                if last_stop.departure_time == math.inf:
                    vehicle_info['last_stop_time'] = last_stop.arrival_time
                    vehicle_info['departure_time'] = last_stop.arrival_time
            else:
                last_stop = route.next_stops[-1]
                vehicle_info['departure_time'] = last_stop.arrival_time
                vehicle_info['departure_stop'] = last_stop.location.label
                vehicle_info['last_stop_time'] = last_stop.arrival_time
                vehicle_info['last_stop'] = last_stop.location.label

            self.vehicle_request_assign[vehicle_id] = vehicle_info

    def calc_reach_time(self, vehicle_info, trip):
        """ Function to calculate the travel time from the last stop of the vehicle route
        """

        reach_time = (vehicle_info['last_stop_time'] + self.durations[vehicle_info['last_stop']][trip.origin.label])
        return max(reach_time, trip.ready_time)

    def create_online_solution(self, X, Y, U, Z):
        """ Function: determine the value of the variables in the model based on vehicle_request_assign dictionary
                      the function is used to check the feasibility of the solution
            Input:
            ------------
                X, Y , U, Z : Model variables
        """
        for veh_id, veh_info in self.vehicle_request_assign.items():
            if len(veh_info['assigned_requests']) != 0:
                trip = veh_info['assigned_requests'][0]
                Y[veh_id][trip.id] = True
                U[trip.id] = max(trip.ready_time, (
                        veh_info['departure_time'] + self.durations[veh_info['departure_stop']][trip.origin.label]))
                Z[trip.id] = True

                if len(veh_info['assigned_requests']) > 1:
                    previous_trip = trip
                    for request in veh_info['assigned_requests'][1:]:
                        X[previous_trip.id][request.id] = True
                        Z[request.id] = True
                        U[request.id] = max(request.ready_time,
                                            (U[previous_trip.id] + previous_trip.shortest_travel_time + self.durations[
                                                previous_trip.destination.label][request.origin.label]))
                        Z[request.id] = True
                        previous_trip = request


    @property
    def vehicle_request_assign(self):
        """Getter for vehicle_request_assign."""
        return self.__vehicle_request_assign

    @property
    def durations(self):
        """Getter for duration."""
        return self.__durations

    @property
    def costs(self):
        """Getter for costs."""
        return self.__costs

    @property
    def algorithm(self):
        """Getter for algorithm."""
        return self.__algorithm

    @property
    def objective(self):
        """Getter for objective."""
        return self.__objective

    @property
    def objective_value(self):
        """Getter for objective_value."""
        return self.__objective_value

    @property
    def total_customers_served(self):
        """Getter for total_customers_served."""
        return self.__total_customers_served

    @objective_value.setter
    def objective_value(self, objective_value):
        """Setter for the objective_value attribute."""
        self.__objective_value = objective_value

    @total_customers_served.setter
    def total_customers_served(self, total_customers_served):
        """Setter for the total_customers_served attribute."""
        self.__total_customers_served = total_customers_served

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

