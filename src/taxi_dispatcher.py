import math
import logging
from src.utilities import Algorithm, Objectives, get_costs, get_durations, get_distances

logger = logging.getLogger(__name__)

from multimodalsim.optimization.dispatcher import Dispatcher, OptimizedRoutePlan
from src.Offline_solver import (create_model, define_objective_total_profit, define_objective_total_customers,
                                define_objective_total_wait_time, solve_offline_model)



class TaxiDispatcher(Dispatcher):
    """Optimize the vehicle routing and the trip-route assignment. This
        method relies on three other methods:
            1. prepare_input
            2. optimize
            3. create_route_plans_list

        Attributes:
        ------------
        boarding_time: int
            The time difference between the arrival and the departure time (10seconds).
        rejected_trips: list
             an array of rideRequests that we are not able to serve them while meeting constraints
        algorithm: Algorithm(Enum)
            The optimization algorithm utilized for planning and assigning trips to vehicles.
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan (e.g., maximizing profit or minimizing wait time).
        total_Profit: float
            The cumulative profit from all served ride requests.
        total_wait_time: float
            The total waiting time experienced by customers.
        total_customers: int
            The count of customers successfully served.
        total_full_driving: float
            The duration vehicles spend driving with passengers.
        total_empty_driving: float
            The duration vehicles spend driving without passengers.
    """

    def __init__(self, network, algorithm, objective):
        """
        Call the constructor

        Input:
        ------------
        network: Network
            The transport network over which the dispatching occurs.
        algorithm: Algorithm(Enum)
            The optimization algorithm to use.
        objective: Objectives(Enum)
            Selected objective as the criterion of evaluating the plan
        """

        super().__init__()
        self.__network = network
        self.__rejected_trips = []
        self.__algorithm = algorithm
        self.__objective = objective
        self.__total_customers_served = 0
        self.__objective_value = 0

    @property
    def objective_value(self):
        """Getter for the objective_value attribute."""
        return self.__objective_value

    @property
    def total_customers_served(self):
        """Getter for the total_customers_served attribute."""
        return self.__total_customers_served

    def __str__(self):
        """ Function: provide a string representation of the TaxiDispatcher,
        detailing rejected trips, the objective value, and the total number of served customers. """

        class_string = ("\nNumber of Rejected Trips: " + str(len(self.__rejected_trips)) + "\n" +
                        "Objective value: " + str(self.__objective_value) + "\n" +
                        "Total Number of served customers: " + str(self.__total_customers_served) + "\n")
        return class_string

    def prepare_input(self, state):
        """ Function: Extract from the state the next legs and the routes that are sent as
            input to the optimize method (i.e. the legs and the routes that
            you want to optimize).

            All next legs and all routes existing in the environment at
            the time of optimization will be optimized.

            Input:
            ------------
                state: An object of type State that corresponds to a partial deep
                    copy of the environment.

            Output:
            ------------
                selected_next_legs: A list of objects of type Trip that correspond
                    to the trips (i.e., passengers or requests) that should be
                    considered by the optimize method.

                selected_routes: A list of objects of type Route that correspond
                    to the routes associated with the vehicles that
                    should be considered by the optimize method.

            Note that if selected_next_legs or selected_routes is empty, no
            optimization will be done.
            """

        selected_route = []
        rejected_ids = {leg.id for leg in self.__rejected_trips}

        # remove rejected trips from the list of non-assigned trips
        state.non_assigned_next_legs = [leg for leg in state.non_assigned_next_legs if leg.id not in rejected_ids]
        selected_next_legs = state.non_assigned_next_legs

        if len(state.non_assigned_next_legs) > 0:
            for vehicle in state.vehicles:
                route = state.route_by_vehicle_id[vehicle.id]
                selected_route.append(route)

        return selected_next_legs, selected_route

    def optimize(self, selected_next_legs, selected_routes, current_time, state):
        """ Function: Determine the vehicle routing and the trip-route assignment
            according to an optimization algorithm. The optimization algorithm
            should be called in this method.

            Input:
            ------------
                selected_next_legs: List of the next legs to be optimized.
                selected_routes: List of the routes to be optimized.
                current_time: int
                Integer equal to the current time of the State.
                The value of current_time is defined as follows:
                    current_time = Environment.current_time + Optimization.freeze_interval.
                    Environment.current_time: The time at which the Optimize event is processed.
                    freeze_interval: 0, by default, see Optimization.freeze_interval
                state: An object of type State that corresponds to a partial deep
                    copy of the environment.

            Output:
            ------------
                optimized_route_plans: List of the optimized route plans. Each route
                plan is an object of type OptimizedRoutePlan.
        """

        vehicles = [route.vehicle for route in selected_routes]
        # non-assigned requests
        trips = [leg.trip for leg in selected_next_legs]
        next_leg_by_trip_id = {leg.trip.id: leg for leg in selected_next_legs}

        # travel time between stop locations
        durations = get_durations(self.__network)
        # driving cost between stop locations
        costs = get_costs(self.__network)

        if self.__algorithm == Algorithm.MIP_SOLVER:
            # create model
            model, Y_var, X_var, Z_var, U_var = create_model(vehicles, trips, durations)

            # add objective
            if self.__objective == Objectives.PROFIT:
                define_objective_total_profit(X_var, Y_var, model, vehicles, trips, costs)
            elif self.__objective == Objectives.TOTAL_CUSTOMERS:
                define_objective_total_customers(Z_var, model, trips)
            elif self.__objective == Objectives.WAIT_TIME:
                define_objective_total_wait_time(U_var, Z_var, model, trips)

            # solve and get solution
            self.__objective_value, veh_trips_assignments_list = solve_offline_model(model, trips, vehicles, Y_var,
                                                                                     X_var, Z_var, U_var,
                                                                                     selected_routes,
                                                                                     self.__rejected_trips)
            # calculate the total number of served customers
            self.__total_customers_served += sum(1 for f_i in trips if round(Z_var[f_i.id].x))

        veh_trips_assignments_list = list(veh_trips_assignments_list.values())
        # remove the vehicles without any changes in request-assign
        veh_trips_assignments_list = [temp_dict for temp_dict in veh_trips_assignments_list if
                                      temp_dict['assigned_requests']]
        route_plans_list = self.__create_route_plans_list(veh_trips_assignments_list, next_leg_by_trip_id, current_time,
                                                          state)

        return route_plans_list

    def __create_route_plans_list(self, veh_trips_assignments_list,
                                  next_leg_by_trip_id, current_time, state):
        """
            Function: Constructs a list of optimized route plans based on vehicle assignments and current state.

                Input:
                ------------
                veh_trips_assignments_list: A list of dictionaries, each representing a
                    vehicle's assigned trips and its last stop.
                next_leg_by_trip_id: A dictionary mapping trip IDs to their corresponding next legs.
                current_time: The current time of the simulation.
                state: The current state of the environment, containing information about vehicles and routes.

                Output:
                ------------
                route_plans_list : A list of OptimizedRoutePlan instances, each representing an optimized route for a vehicle.
        """
        route_plans_list = []
        for veh_trips_assignment in veh_trips_assignments_list:
            trip_ids = [trip.id for trip in
                        veh_trips_assignment['assigned_requests']]

            route = state.route_by_vehicle_id[
                veh_trips_assignment["vehicle"].id]
            route_plan = self.__create_route_plan(route, trip_ids,
                                                  veh_trips_assignment['last_stop'].location.label,
                                                  next_leg_by_trip_id,
                                                  current_time)
            route_plans_list.append(route_plan)

        return route_plans_list

    def __create_route_plan(self, route, trip_ids, departure_stop_id,
                            next_leg_by_trip_id, current_time):
        """
            Function: Creates an optimized route plan for a vehicle based on assigned trips and current state.

                Input:
                ------------
                route: The current route of the vehicle.
                trip_ids: A list of trip IDs assigned to the vehicle.
                departure_stop_id: The ID of the stop from which the vehicle will depart.
                next_leg_by_trip_id: A dictionary mapping trip IDs to their corresponding next legs.
                current_time: The current time of the simulation.

                Output:
                ------------
                OptimizedRoutePlan : An optimized route plan for the vehicle.
        """

        route_plan = OptimizedRoutePlan(route)

        if len(route.next_stops) == 0:
            # If the current route has no stops, update the departure time of the current stop to the current time.
            route_plan.update_current_stop_departure_time(current_time)
            departure_time = current_time
        else:
            # If there are existing stops, set the departure time of the last stop to its arrival time.
            route.next_stops[-1].departure_time = route.next_stops[-1].arrival_time
            departure_time = route.next_stops[-1].departure_time
            route_plan.copy_route_stops()

        for index, trip_id in enumerate(trip_ids):
            leg = next_leg_by_trip_id[trip_id]
            route_plan.assign_leg(leg)
            # Calculate and add pick-up stop.
            arrival_time = departure_time + self.__network.nodes[departure_stop_id]['shortest_paths'][
                leg.trip.origin.label]['total_duration']
            if arrival_time < leg.trip.ready_time:
                # If the vehicle arrives earlier than the ready time, adjust departure to align with the ready time.
                if len(route.next_stops) == 0:
                    route_plan.update_current_stop_departure_time(current_time + leg.trip.ready_time - arrival_time)
                else:
                    route_plan.next_stops[-1].departure_time += leg.trip.ready_time - arrival_time
                arrival_time = leg.trip.ready_time
            departure_time = arrival_time
            route_plan.append_next_stop(leg.trip.origin.label, arrival_time, departure_time)

            # Calculate and add drop-off stop.
            arrival_time = departure_time + leg.trip.shortest_travel_time
            departure_time = arrival_time if index != len(trip_ids) - 1 else math.inf
            route_plan.append_next_stop(leg.trip.destination.label, arrival_time, departure_time)

        return route_plan

    def extract_output(self):
        """
            Function: Extracts and summarizes output information regarding the dispatch operation.

                Output:
                ------------
                output_dict: A dictionary containing details about the algorithm used, the optimization objective,
                    the objective value, the number of served customers, and the percentage of service.
                """
        total_trips = self.total_customers_served + len(self.__rejected_trips)
        output_dict = {
            'Algorithm': self.__algorithm.value,
            'Objective_type': self.__objective.value,
            'Objective_value' : self.objective_value,
            '# served customers' : self.total_customers_served,
            '% of Service': (self.total_customers_served / total_trips * 100).__round__(1)
        }
        return output_dict

