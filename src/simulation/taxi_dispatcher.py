import math
import logging
from typing import List, Any

from multimodalsim.optimization.dispatcher import Dispatcher, OptimizedRoutePlan
from src.utilities.config import SimulationConfig
from src.utilities.enums import Algorithm, Objectives
from src.utilities.tools import SolutionMode
from src.utilities.timer import Timer

logger = logging.getLogger(__name__)

class TaxiDispatcher(Dispatcher):
    """Optimize the vehicle routing and the trip-route assignment. This method relies on three other methods:
            1. prepare_input
            2. optimize
            3. create_route_plans_list

        Attributes:
        ------------
        network: Network
            The transport network over which the dispatching occurs.
        simulation_config : SimulationConfig
            Configuration object containing all simulation parameters.
        rejected_trips: list
             an array of rideRequests that we are not able to serve them while meeting constraints
        total_customers_served: int
            The count of customers successfully served.
        total_profit: float
            The total profit of customers successfully served.
        total_waiting_time: float
            The total waiting time of the solution.
        objective_value: int
            The objective value from served requests.
        runtime : Timer
            Timer to keep track on the time to optimize the solution
        current_solution: Dict
            the current solution for re-optimization purpose
        solver: solver object
            the solver class including the optimizing functions


    """

    def __init__(self,
                 network: Any,
                 vehicles: List[Any],
                 simulation_config: SimulationConfig):
        """
        Call the constructor

        Input:
        ------------
        network: The transport network over which the dispatching occurs.
        vehicles: Set of input vehicles
        simulation_config : Configuration object containing all simulation parameters.
        """

        super().__init__()
        self.network = network
        self.simulation_config = simulation_config
        self.rejected_trips: List[Any] = []
        self.objective_value: float = 0.0
        self.total_customers_served: int = 0
        self.total_profit: float = 0.0
        self.total_waiting_time: float = 0.0
        self.current_solution = None
        self.runtime = Timer()

        # Initialize the appropriate solver based on the algorithm
        self.solver = self._initialize_solver(vehicles)

    def _initialize_solver(
            self,
            vehicles: List[Any],
    ) -> Any:
        """
        Factory method to initialize the appropriate solver based on the algorithm.

        Parameters:
        -----------
        vehicles: List[Any]
            List of input vehicles.

        Returns:
        --------
        Any
            An instance of the appropriate solver class.
        """
        algorithm = self.simulation_config.algorithm

        if algorithm == Algorithm.MIP_SOLVER:
            from src.solvers.solver import Solver
            return Solver(network=self.network, vehicles=vehicles, simulation_config=self.simulation_config)
        elif algorithm == Algorithm.CONSENSUS:
            from src.solvers.stochastic_solver import StochasticSolver
            return StochasticSolver(network=self.network, vehicles=vehicles, simulation_config=self.simulation_config)
        elif algorithm == Algorithm.RE_OPTIMIZE:
            from src.solvers.re_optimizer import ReOptimizer
            return ReOptimizer(network=self.network, vehicles=vehicles, simulation_config=self.simulation_config)
        else:
            from src.solvers.online_solver import OnlineSolver
            return OnlineSolver(network=self.network, vehicles=vehicles, simulation_config=self.simulation_config)

    def __str__(self) -> str:
        """Provide a string representation of the TaxiDispatcher."""
        return (
            f"\nNumber of Rejected Trips: {len(self.rejected_trips)}\n"
            f"Objective value: {self.objective_value}\n"
            f"Total Number of served customers: {self.total_customers_served}\n"
            f"Total Profit: {self.total_profit}\n"
            f"Total Waiting time: {self.total_waiting_time}\n"
        )


    def prepare_input(self, state: Any) -> tuple[List[Any], List[Any]]:
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

            Note that if selected_next_legs or selected_routes is empty, no optimization will be done.
            """

        selected_route = []
        self.rejected_trips = [
            leg.trip for leg in state.non_assigned_next_legs
            if leg.trip.latest_pickup < state.current_time
        ]
        rejected_ids = {trip.id for trip in self.rejected_trips}

        # remove rejected trips from the list of non-assigned trips
        selected_next_legs = [
            leg for leg in state.non_assigned_next_legs
            if leg.trip.id not in rejected_ids
        ]

        if selected_next_legs:
            for vehicle in state.vehicles:
                route = state.route_by_vehicle_id[vehicle.id]
                if self.simulation_config.algorithm != Algorithm.CONSENSUS or len(route.next_stops) <= 1:
                    selected_route.append(route)
        current_routes = [state.route_by_vehicle_id[vehicle.id] for vehicle in state.vehicles]
        self.solver.update_vehicle_state(current_routes, state.current_time)
        return selected_next_legs, selected_route

    def optimize(
            self,
            selected_next_legs: List[Any],
            selected_routes: List[Any],
            current_time: int,
            state: Any
    ) -> List[OptimizedRoutePlan]:

        """
        Function: Determine the vehicle routing and the trip-route assignment
            according to an optimization algorithm. The optimization algorithm
            should be called in this method.

            Input:
            ------------
                selected_next_legs: List[Any]
                    List of the next legs to be optimized.
                selected_routes: List[Any]
                    List of the routes to be optimized.
                current_time: int
                    Current time of the simulation.
                state: Any
                An object of type State that corresponds to a partial deep copy of the environment.

            Output:
            ------------
                optimized_route_plans: List of the optimized route plans. Each route
                plan is an object of type OptimizedRoutePlan.
        """
        self.runtime.start()

        vehicles = [route.vehicle for route in selected_routes]
        # non-assigned requests
        trips = [leg.trip for leg in selected_next_legs]
        trips = sorted(trips, key=lambda x: x.ready_time)
        next_leg_by_trip_id = {leg.trip.id: leg for leg in selected_next_legs}

        if self.simulation_config.algorithm == Algorithm.MIP_SOLVER:
            from src.solvers.offline_solver import OfflineSolver
            # create and  optimize MIP model
            offline_model = OfflineSolver(self.network, self.solver.objective)
            offline_model.offline_solver(vehicles, trips, self.solver.vehicle_request_assign, self.rejected_trips)

        else:
            K = [vehicle_dict['vehicle'] for vehicle_dict in self.solver.vehicle_request_assign.values()]
            self.solver.variables_declaration(K, trips)
            if self.simulation_config.algorithm == Algorithm.CONSENSUS:
                self.solver.stochastic_solver(vehicles, trips, current_time)
            elif self.simulation_config.algorithm == Algorithm.RE_OPTIMIZE:
                self.solver.re_optimizer(vehicles, trips, self.rejected_trips)
            else:
                self.solver.online_solver(vehicles, trips, self.rejected_trips)


        veh_trips_assignments_list = list(self.solver.vehicle_request_assign.values())
        # remove the vehicles without any changes in request-assign
        veh_trips_assignments_list = [temp_dict for temp_dict in veh_trips_assignments_list if
                                      temp_dict['assigned_requests']]
        route_plans_list = self.__create_route_plans_list(veh_trips_assignments_list, next_leg_by_trip_id,
                                                          current_time, state)
        self.runtime.stop()
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
            trip_ids = [trip.id for trip in veh_trips_assignment['assigned_requests']]

            route = state.route_by_vehicle_id[
                veh_trips_assignment["vehicle"].id]
            if self.simulation_config.solution_mode == SolutionMode.OFFLINE or len(route.next_stops) <= 1:
                route_plan = self.__create_route_plan(route, trip_ids, veh_trips_assignment['departure_stop'],
                                                      next_leg_by_trip_id, current_time)
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

        route_plan = OptimizedRoutePlan(route)

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
            if self.simulation_config.solution_mode != SolutionMode.OFFLINE and len(route_plan.assigned_legs) > 0:
                break

            leg = next_leg_by_trip_id[trip_id]

            # Calculate and add pick-up stop.
            travel_time_to_pick = self.network.nodes[departure_stop_id]['shortest_paths'][
                leg.trip.origin.label]['total_duration']
            arrival_time = departure_time + travel_time_to_pick
            if arrival_time < leg.trip.ready_time:
                if self.simulation_config.solution_mode != SolutionMode.OFFLINE:
                    break
                # If the vehicle arrives earlier than the ready time, adjust departure to align with the ready time.
                if len(route_plan.next_stops) == 0:
                    route_plan.update_current_stop_departure_time(current_time + leg.trip.ready_time - arrival_time)
                else:
                    route_plan.next_stops[-1].departure_time += leg.trip.ready_time - arrival_time
                arrival_time = leg.trip.ready_time
            departure_time = arrival_time
            route_plan.append_next_stop(leg.trip.origin.label, arrival_time, departure_time, legs_to_board=[leg])
            route_plan.assign_leg(leg)
            # update objectives
            self.total_customers_served += 1
            self.total_profit += (leg.trip.fare - (leg.trip.shortest_travel_time + travel_time_to_pick)/ 3600 * 5)
            self.total_waiting_time += arrival_time - leg.trip.ready_time
            if self.solver.objective == Objectives.TOTAL_CUSTOMERS:
                self.objective_value += 1

            elif self.solver.objective == Objectives.WAIT_TIME:
                self.objective_value += arrival_time - leg.trip.ready_time

            elif self.solver.objective == Objectives.TOTAL_PROFIT:
                self.objective_value += (leg.trip.fare - (leg.trip.shortest_travel_time + travel_time_to_pick)/ 3600 * 5)


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
        total_trips = self.total_customers_served + len(self.rejected_trips)
        for trip in self.rejected_trips:
            self.total_waiting_time += trip.latest_pickup - trip.ready_time
            if self.solver.objective == Objectives.WAIT_TIME:
                self.objective_value += trip.latest_pickup - trip.ready_time

        percentage_service = (self.total_customers_served / total_trips * 100) if total_trips > 0 else 0
        percentage_service = round(percentage_service, 1)

        output_dict = {
            'Algorithm': self.simulation_config.algorithm.value,
            'Objective type': self.simulation_config.objective.value,
            'Objective value' : round(self.objective_value, 2),
#            '# Served customers' : self.total_customers_served,
            'Average profit ($)': round(self.total_profit/total_trips, 2),
#            'Total profit': round(self.total_profit,2),
 #           'Total waiting time': round(self.total_waiting_time,2),
            'Average waiting time (s)': round(self.total_waiting_time/total_trips, 2),
            '% of Service': percentage_service,
            'optimization_time (s)': round(self.runtime.elapsed_since_init(),3)
        }
        return output_dict


