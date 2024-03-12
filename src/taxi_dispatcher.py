import math
import logging

from multimodalsim.optimization.optimization import OptimizationResult
from multimodalsim.simulator.vehicle import Stop, LabelLocation

from src.utilities import Algorithm, Objectives, SolutionMode, get_costs, get_durations

logger = logging.getLogger(__name__)

from multimodalsim.optimization.dispatcher import Dispatcher
from src.Offline_solver import (create_model, define_objective_total_customers,define_objective_total_profit,
                                define_objective_total_wait_time, solve_offline_model, define_objective)
from src.constraints_and_objectives import variables_declaration
from src.Online_solver import OnlineSolver
from src.stochastic_solver import StochasticSolver
from src.solver import Solver



class TaxiDispatcher(Dispatcher):
    """Optimize the vehicle routing and the trip-route assignment. This
        method relies on three other methods:
            1. prepare_input
            2. optimize
            3. create_route_plans_list

        Attributes:
        ------------
        network: Network
            The transport network over which the dispatching occurs.
        rejected_trips: list
             an array of rideRequests that we are not able to serve them while meeting constraints
        algorithm: Algorithm(Enum)
            The optimization algorithm utilized for planning and assigning trips to vehicles.
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan (e.g., maximizing profit or minimizing wait time).
        objective_value: float
            The total objective value from all served ride requests.
        total_customers_served: int
            The count of customers successfully served.
        solver: solver object
            the solver class including the optimizing functions
        solution_mode : SolutionMode(Enum)
            The mode of solution

    """

    def __init__(self, network, algorithm, objective, vehicles, solution_mode, nb_scenario=None, cust_node_hour=None):
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
        vehicles: Set of input vehicles
        solution_mode : The mode of solution
        """

        super().__init__()
        self.__network = network
        self.__rejected_trips = []
        self.__algorithm = algorithm
        self.__objective = objective
        self.__total_customers_served = 0
        self.__objective_value = 0
        self.__solution_mode = solution_mode
        if solution_mode == SolutionMode.OFFLINE:
            self.__solver = Solver(network, algorithm, objective, vehicles)
        else:
            if algorithm == Algorithm.QUALITATIVE_CONSENSUS or algorithm == Algorithm.QUANTITATIVE_CONSENSUS:
                self.__solver = StochasticSolver(network, algorithm, objective, vehicles, nb_scenario, cust_node_hour)
            else:
                self.__solver = OnlineSolver(network, algorithm, objective, vehicles)

    @property
    def objective_value(self):
        """Getter for the objective_value attribute."""
        return self.__objective_value

    @property
    def solution_mode(self):
        """Getter for the solution_mode attribute."""
        return self.__solution_mode

    @property
    def total_customers_served(self):
        """Getter for the total_customers_served attribute."""
        return self.__total_customers_served

    @property
    def solver(self):
        """Getter for solver"""
        return self.__solver

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

                vehicle_request_assign: dictionary containing vehicle-request assignments.

            Note that if selected_next_legs or selected_routes is empty, no
            optimization will be done.
            """

        selected_route = []
        if self.__algorithm == Algorithm.QUALITATIVE_CONSENSUS or self.__algorithm == Algorithm.QUANTITATIVE_CONSENSUS:
            self.__rejected_trips = [leg.trip for leg in state.non_assigned_next_legs if leg.trip.latest_pickup
                                     < state.current_time]
        rejected_ids = {leg.id for leg in self.__rejected_trips}

        # remove rejected trips from the list of non-assigned trips
        selected_next_legs = [leg for leg in state.non_assigned_next_legs if leg.id not in rejected_ids]

        if len(state.non_assigned_next_legs) > 0:
            for vehicle in state.vehicles:
                route = state.route_by_vehicle_id[vehicle.id]
                if self.__algorithm != Algorithm.QUALITATIVE_CONSENSUS and self.__algorithm != Algorithm.QUANTITATIVE_CONSENSUS:
                    selected_route.append(route)
                elif len(route.next_stops) <= 1:
                    selected_route.append(route)
        current_routes = [state.route_by_vehicle_id[vehicle.id] for vehicle in state.vehicles]
        self.solver.update_vehicle_state(current_routes)
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
            model, Y_var, X_var, Z_var, U_var = create_model(vehicles, trips, durations,
                                                             self.solver.vehicle_request_assign)

            # add objective
            define_objective(self.__objective, X_var, Y_var, U_var, Z_var, model, vehicles, trips, costs,
                             self.solver.vehicle_request_assign)

            # solve and get solution
            obj_value = solve_offline_model(model, trips, vehicles, Y_var, X_var, Z_var,
                                            self.__rejected_trips, self.solver.vehicle_request_assign)
            self.__objective_value += obj_value
            # calculate the total number of served customers
            self.__total_customers_served += sum(1 for f_i in trips if round(Z_var[f_i.id].x))
        else:
            K = [vehicle_dict['vehicle'] for vehicle_dict in self.solver.vehicle_request_assign.values()]
            X, Y, U, Z = variables_declaration(K, trips)
            if self.__algorithm == Algorithm.QUALITATIVE_CONSENSUS or self.__algorithm == Algorithm.QUANTITATIVE_CONSENSUS:
                self.solver.stochastic_solver(vehicles, trips, Y, X, Z, U, self.__network, current_time)
            else:
                self.solver.online_solver(vehicles, trips, Y, X, Z, U, self.__rejected_trips)

            self.__objective_value += self.solver.objective_value
            # calculate the total number of served customers
            self.__total_customers_served += self.solver.total_customers_served

        veh_trips_assignments_list = list(self.solver.vehicle_request_assign.values())
        # remove the vehicles without any changes in request-assign
        veh_trips_assignments_list = [temp_dict for temp_dict in veh_trips_assignments_list if
                                      temp_dict['assigned_requests']]
        route_plans_list = self.__create_route_plans_list(veh_trips_assignments_list, next_leg_by_trip_id,
                                                          current_time, state)

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
                                                  veh_trips_assignment['departure_stop'],
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
                departure_stop_id: The ID of the location from which the vehicle will depart.
                next_leg_by_trip_id: A dictionary mapping trip IDs to their corresponding next legs.
                current_time: The current time of the simulation.

                Output:
                ------------
                OptimizedRoutePlan : An optimized route plan for the vehicle.
        """

        route_plan = OptimizedRoutePlanNew(route)

        if len(route.next_stops) == 0:
            # If the current route has no stops, update the departure time of the current stop to the current time.
            last_stop = route.previous_stops[-1] if route.current_stop is None else route.current_stop
            if last_stop.departure_time < current_time or last_stop.departure_time == math.inf:
                last_stop.departure_time = current_time
            departure_time = last_stop.departure_time
            route_plan.update_current_stop_departure_time(departure_time)
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
                if len(route_plan.next_stops) == 0:
                    route_plan.update_current_stop_departure_time(current_time + leg.trip.ready_time - arrival_time)
                else:
                    route_plan.next_stops[-1].departure_time += leg.trip.ready_time - arrival_time
                arrival_time = leg.trip.ready_time
            departure_time = arrival_time
            route_plan.append_next_stop(leg.trip.origin.label, arrival_time, departure_time, legs_to_board=[leg])

            # Calculate and add drop-off stop.
            arrival_time = departure_time + leg.trip.shortest_travel_time
            departure_time = arrival_time if index != len(trip_ids) - 1 else math.inf
            route_plan.append_next_stop(leg.trip.destination.label, arrival_time, departure_time, legs_to_alight=[leg])
            departure_stop_id = leg.trip.destination.label

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
            'Objective_value' : self.objective_value.__round__(2),
            '# served customers' : self.total_customers_served,
            '% of Service': (self.total_customers_served / total_trips * 100).__round__(1)
        }
        return output_dict


    def process_optimized_route_plans(self, optimized_route_plans, state):
        """Create and modify the simulation objects that correspond to the
        optimized route plans returned by the optimize method. In other words,
        this method "translates" the results of optimization into the
        "language" of the simulator.

        Input:
          -optimized_route_plans: List of objects of type OptimizedRoutePlan
           that correspond to the results of the optimization.
          -state: An object of type State that corresponds to a partial deep
           copy of the environment.
        Output:
          -optimization_result: An object of type OptimizationResult that
           consists essentially of a list of the modified trips, a list of
           the modified vehicles and a copy of the (possibly modified) state.
        """

        modified_trips = []
        modified_vehicles = []

        for route_plan in optimized_route_plans:
            self.__process_route_plan(route_plan)

            trips = [leg.trip for leg in route_plan.assigned_legs]

            modified_trips.extend(trips)
            modified_vehicles.append(route_plan.route.vehicle)

        optimization_result = OptimizationResult(state, modified_trips,
                                                 modified_vehicles)

        return optimization_result

    def __process_route_plan(self, route_plan):

        self.__update_route_next_stops(route_plan)

        for leg in route_plan.already_onboard_legs:
            # Assign leg to route
            route_plan.route.assign_leg(leg)

            # Assign the trip associated with leg that was already on board
            # before optimization took place to the stops of the route
            self.__assign_already_onboard_trip_to_stop(leg, route_plan.route)

        for leg in route_plan.assigned_legs:
            # Assign leg to route
            route_plan.route.assign_leg(leg)

            # Assign the trip associated with leg to the stops of the route
            if leg not in route_plan.legs_manually_assigned_to_stops \
                    and leg not in route_plan.already_onboard_legs:
                self.__automatically_assign_trip_to_stops(leg,
                                                          route_plan.route)

    def __update_route_next_stops(self, route_plan):
        # Update current stop departure time
        if route_plan.route.current_stop is not None:
            route_plan.route.current_stop.departure_time = \
                route_plan.current_stop_departure_time

        route_plan.route.next_stops = route_plan.next_stops

        # Last stop departure time is set to infinity (since it is unknown).
        if route_plan.next_stops is not None \
                and len(route_plan.next_stops) > 0:
            route_plan.route.next_stops[-1].departure_time = math.inf

    def __automatically_assign_trip_to_stops(self, leg, route):

        boarding_stop_found = False
        alighting_stop_found = False

        if route.current_stop is not None:
            current_location = route.current_stop.location

            if leg.origin == current_location:
                route.current_stop.passengers_to_board.append(leg.trip)
                boarding_stop_found = True

        for stop in route.next_stops:
            if leg.origin == stop.location and not boarding_stop_found:
                stop.passengers_to_board.append(leg.trip)
                boarding_stop_found = True
            elif leg.destination == stop.location and boarding_stop_found \
                    and not alighting_stop_found:
                stop.passengers_to_alight.append(leg.trip)
                alighting_stop_found = True

    def __assign_already_onboard_trip_to_stop(self, leg, route):

        for stop in route.next_stops:
            if leg.destination == stop.location:
                stop.passengers_to_alight.append(leg.trip)
                break

class OptimizedRoutePlanNew:
    """Structure to store the optimization results of one route.

        Attributes:
            route: object of type Route
                The route that will be modified according to the route plan.
            current_stop_departure_time: int or float
                The planned departure time of the current stop of the route.
            next_stops: list of objects of type Stop
                The planned next stops of the route.
            assigned_legs: list of objects of type Leg.
                The legs planned to be assigned to the route.

        Remark:
            If the parameter next_stops of __init__ is None and no stop is
            appended through the append_next_stop method, then the original
            stops of the route will not be modified (see FixedLineDispatcher
            for an example).

    """

    def __init__(self, route, current_stop_departure_time=None,
                 next_stops=None, assigned_legs=None):
        """
        Parameters:
            route: object of type Route
                The route that will be modified according to the route plan.
            current_stop_departure_time: int, float or None
                The planned departure time of the current stop of the route.
            next_stops: list of objects of type Stop or None
                The planned next stops of the route.
            assigned_legs: list of objects of type Leg or None
                The legs planned to be assigned to the route.
        """

        self.__route = route
        self.__current_stop_departure_time = current_stop_departure_time
        self.__next_stops = next_stops if next_stops is not None else []
        self.__assigned_legs = assigned_legs if assigned_legs is not None \
            else []

        self.__already_onboard_legs = []

        self.__legs_manually_assigned_to_stops = []

    @property
    def route(self):
        return self.__route

    @property
    def current_stop_departure_time(self):
        return self.__current_stop_departure_time

    @property
    def next_stops(self):
        return self.__next_stops

    @property
    def assigned_legs(self):
        return self.__assigned_legs

    @property
    def already_onboard_legs(self):
        return self.__already_onboard_legs

    @property
    def legs_manually_assigned_to_stops(self):
        return self.__legs_manually_assigned_to_stops

    def update_current_stop_departure_time(self, departure_time):
        """Modify the departure time of the current stop of the route plan
        (i.e., the stop at which the vehicle is at the time of optimization).
            Parameter:
                departure_time: int
                    New departure time of the current stop.
        """
        self.__current_stop_departure_time = departure_time

    def append_next_stop(self, stop_id, arrival_time, departure_time=None,
                         lon=None, lat=None, cumulative_distance=None,
                         legs_to_board=None, legs_to_alight=None):
        """Append a stop to the list of next stops of the route plan.
            Parameters:
                stop_id: string
                    Label of a stop location.
                arrival_time: int
                    Time at which the vehicle is planned to arrive at the stop.
                departure_time: int or None
                    Time at which the vehicle is panned to leave the stop.
                    If None, then departure_time is set equal to arrival_time.
                lon: float
                    Longitude of the stop. If None, then the stop has no
                    longitude.
                lat: float
                    Latitude of the stop. If None, then the stop has no
                    latitude.
                cumulative_distance: float
                    Cumulative distance that the vehicle will have travelled
                    when it arrives at the stop.
                legs_to_board: list of objects of type Leg or None
                    The legs that should be boarded at that stop. If None, then
                    the legs that are not explicitly assigned to a stop will
                    automatically be boarded at the first stop corresponding to
                    the origin location.
                legs_to_alight: list of objects of type Leg or None
                    The legs that should be alighted at that stop. If None,
                    then the legs that are not explicitly assigned to a stop
                    will automatically be alighted at the first stop
                    corresponding to the destination location.
        """
        if self.__next_stops is None:
            self.__next_stops = []

        if departure_time is None:
            departure_time = arrival_time

        stop = Stop(arrival_time, departure_time,
                    LabelLocation(stop_id, lon, lat),
                    cumulative_distance=cumulative_distance)

        if legs_to_board is not None:
            self.__assign_legs_to_board_to_stop(legs_to_board, stop)

        if legs_to_alight is not None:
            self.__assign_legs_to_alight_to_stop(legs_to_alight, stop)

        self.__next_stops.append(stop)

        return self.__next_stops

    def assign_leg(self, leg):
        """Append a leg to the list of assigned legs of the route plan.
            Parameter:
                leg: object of type Leg
                    The leg to be assigned to the route.
        """

        leg.assigned_vehicle = self.route.vehicle

        if leg not in self.__assigned_legs:
            self.__assigned_legs.append(leg)

        return self.__assigned_legs

    def copy_route_stops(self):
        """Copy the current and next stops of the route to the current and
        next stops of OptimizedRoutePlan, respectively."""

        if self.route.current_stop is not None:
            self.__current_stop_departure_time = \
                self.route.current_stop.departure_time

        self.__next_stops = self.route.next_stops

    def assign_already_onboard_legs(self):
        """The legs that are on board will automatically be alighted at the
        first stop corresponding to the destination location."""
        self.__already_onboard_legs.extend(self.route.onboard_legs)

    def __assign_legs_to_board_to_stop(self, legs_to_board, stop):
        for leg in legs_to_board:
            stop.passengers_to_board.append(leg.trip)
            if leg not in self.__legs_manually_assigned_to_stops:
                self.__legs_manually_assigned_to_stops.append(leg)
                self.assign_leg(leg)

    def __assign_legs_to_alight_to_stop(self, legs_to_alight, stop):
        for leg in legs_to_alight:
            stop.passengers_to_alight.append(leg.trip)
            if leg not in self.__legs_manually_assigned_to_stops:
                self.__legs_manually_assigned_to_stops.append(leg)
                self.assign_leg(leg)


