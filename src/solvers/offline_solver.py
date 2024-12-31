import logging
from typing import Any, Dict, Tuple
import gurobipy as gp
from gurobipy import GRB

from src.utilities.enums import Objectives
from src.utilities.tools import get_durations, get_costs


class OfflineSolver:
    """
    A class to solve the taxi routing problem using a MIP solver (Gurobi).

        Attributes:
        ------------
        objective: Objectives(Enum)
            The objective used to evaluate the effectiveness of the plan
        duration : dictionary
            travel time matrix between possible stop points
        costs: dictionary
            driving costs
        model: gp.Model
            The Gurobi model for optimization.
        X_var: Dict[Tuple[int, int], gp.Var]
            Decision variables for trip connections.
        Y_var: Dict[Tuple[int, int], gp.Var]
            Decision variables for assigning trips to vehicles.
        Z_var: Dict[int, gp.Var]
            Decision variables indicating if a trip is served.
        U_var: Dict[int, gp.Var]
            Decision variables for departure times from locations.
        """

    def __init__(self,
                 network: Any,
                 objective: Objectives
                 ) -> None:
        self.objective = objective

        self.objective_value = 0
        self.durations = get_durations(network)
        self.costs = get_costs(network)

        self.model = gp.Model("TaxiRoutingModel")
        # Set OutputFlag based on the logging level
        if logging.getLogger().getEffectiveLevel() > logging.INFO:
            self.model.setParam('OutputFlag', 0)  # Disable solver output
        else:
            self.model.setParam('OutputFlag', 1)  # Enable solver output
        self.X_var: Dict[Tuple[int, int], gp.Var] = {}  # Decision variables for trip connections between customers
        self.Y_var: Dict[Tuple[int, int], gp.Var] = {}  # Decision variables for assigning customers to vehicles
        self.Z_var: Dict[int, gp.Var] = {}  # Decision variables for whether a customer is served
        self.U_var: Dict[int, gp.Var] = {}  # Decision variables for departure times from customer locations

    def define_objective(self, K, P, vehicle_request_assign):
        """Define the objective function based on the selected objective."""
        if self.objective == Objectives.TOTAL_PROFIT:
            self.define_total_profit_objective(K, P, vehicle_request_assign)
        elif self.objective == Objectives.TOTAL_CUSTOMERS:
            self.define_total_customers_objective(P)
        elif self.objective == Objectives.WAIT_TIME:
            self.define_total_wait_time_objective(P)
        else:
            raise ValueError(f"Objective {self.objective} not recognized.")

    def define_total_customers_objective(self, P):
        """ Function: define objective of maximizing the total number of served customers and add it to the model
        Input:
        ------------
            P : set of customers to serve
            model : The Gurobi model to optimize.
            Z_var : Model variables
        """
        self.model.setObjective(
            sum(self.Z_var[f_i.id] for f_i in P),
            sense=GRB.MAXIMIZE
        )

    def define_total_profit_objective(self, K, P, vehicle_request_assign):
        """ Function: define objective of maximizing the total profit and add it to the model
        Input:
        ------------
            K : set of vehicles
            P : set of customers to serve
            vehicle_request_assign: dictionary containing vehicle-request assignments.
        """
        raise NotImplementedError("OfflineSolver.define_total_profit_objective() not implemented")
        model.setObjective(
            """you should write your objective here ..."""
        )

    def define_total_wait_time_objective(self, P):
        """ Function: define objective of minimizing the total wait time and add it to the model
        Input:
        ------------
            P : set of customers to serve
        """
        raise NotImplementedError("OfflineSolver.define_total_wait_time_objective() not implemented")
        model.setObjective(
            """you should write your objective here ..."""
        )

    def create_model(self, K, P, vehicle_request_assign):
        """ Function: create model to solve with Gurobi Solver
            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                vehicle_request_assign: dictionary containing vehicle-request assignments.
        """

        for f_i in P:
            self.U_var[f_i.id] = self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, obj=0, name=f'U_{f_i.id}')
            self.Z_var[f_i.id] = self.model.addVar(vtype=GRB.BINARY, obj=0, name=f'Z_{f_i.id}')
            for f_j in P:
                if f_i != f_j:
                    self.X_var[f_i.id, f_j.id] = self.model.addVar(vtype=GRB.BINARY, name=f'X_{f_i.id}_{f_j.id}')

        for f_i in P:
            for f_k in K:
                self.Y_var[f_k.id, f_i.id] = self.model.addVar(vtype=GRB.BINARY, name=f'Y_{f_k.id}_{f_i.id}')

        # Update the model to include the new variables
        self.model.update()

        """Set up constraints"""
        # Constraints 1
        for f_i in P:
            self.model.addConstr(
                self.Z_var[f_i.id] == sum(self.Y_var[f_k.id, f_i.id] for f_k in K)
                + sum(self.X_var[f_j.id, f_i.id] for f_j in P if f_i != f_j),
                name=f"Constraint1_{f_i.id}"
            )

        # Constraints 2
        for f_i in P:
            self.model.addConstr(
                self.Z_var[f_i.id] >= sum(self.X_var[f_i.id, f_j.id] for f_j in P if f_i != f_j),
                name=f"Constraint2_{f_i.id}"
            )

        # Constraints 3
        for f_k in K:
            self.model.addConstr(
                sum(self.Y_var[f_k.id, f_i.id] for f_i in P) <= 1,
                name=f"Constraint3_{f_k.id}"
            )

        # Constraints 4
        for f_i in P:
            self.model.addConstr(self.U_var[f_i.id] >= f_i.ready_time, name=f"Constraint4a_{f_i.id}")
            self.model.addConstr(self.U_var[f_i.id] <= f_i.latest_pickup, name=f"Constraint4b_{f_i.id}")

        # Constraints 5
        for f_i in P:
            for f_j in P:
                if f_i != f_j:
                    T_ij = f_i.shortest_travel_time + self.durations[f_i.destination.label][f_j.origin.label]
                    delta = f_j.ready_time - f_i.latest_pickup
                    self.model.addConstr(
                        self.U_var[f_j.id] - self.U_var[f_i.id] >= delta + self.X_var[f_i.id, f_j.id] * (T_ij - delta),
                        name=f"Constraint5_{f_i.id}_{f_j.id}"
                    )

        # Constraints 6
        for f_i in P:
            for f_k in K:
                T_ki = self.durations[vehicle_request_assign[f_k.id]['departure_stop']][f_i.origin.label]
                delta = vehicle_request_assign[f_k.id]['departure_time'] + T_ki - f_i.ready_time
                self.model.addConstr(
                    self.U_var[f_i.id] >= f_i.ready_time + delta * self.Y_var[f_k.id, f_i.id],
                    name=f"Constraint6_{f_i.id}_{f_k.id}"
                )
        self.model.update()

    def solve(self):
        """
        Optimize the model using Gurobi.
        """
        self.model.optimize()

        # Check if the optimization was successful
        if self.model.status != GRB.OPTIMAL:
            print("Optimization did not converge to an optimal solution.")
            return
        self.objective_value = round(self.model.objVal, 3)

    def extract_solution(self, K, P, rejected_trips, vehicle_request_assign):
        """
        Function: Extract the solution from the optimized model and Retrieve the variable values
                    convert solution to vehicle_request_assign dictionary which is required to determine the route plan
            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                rejected_trips : List of trips that are rejected in the optimization process.
                vehicle_request_assign: dictionary containing vehicle-request assignments.

            Output:
            ------------
                model.objVal: The objective value of the optimized model

        """

        # Extract the solution and populate the vehicle_request_assign and rejected_trips
        for f_k in K:
            for trip in P:
                if self.Y_var[f_k.id, trip.id].X > 0.5:
                    vehicle_request_assign[f_k.id]['assigned_requests'].append(trip)
                    current_trip = trip
                    while True:
                        next_trip_found = False
                        for f_j in P:
                            if current_trip != f_j and self.X_var[current_trip.id, f_j.id].X > 0.5:
                                vehicle_request_assign[f_k.id]['assigned_requests'].append(f_j)
                                current_trip = f_j
                                next_trip_found = True
                                break
                        if not next_trip_found:
                            break

        for trip in P:
            if self.Z_var[trip.id].X < 0.5:
                rejected_trips.append(trip)

    def offline_solver(self, K, P, vehicle_request_assign, rejected_trips):
        """
        Function:  solve the taxi routing problem using a MIP solver (Gurobi).
            Input:
            ------------
                K : set of vehicles
                P : set of customers to serve
                vehicle_request_assign: dictionary containing vehicle-request assignments.
                rejected_trips : List of trips that are rejected in the optimization process.
        """
        self.create_model(K, P, vehicle_request_assign)
        self.define_objective(K, P, vehicle_request_assign)
        self.solve()
        self.extract_solution(K, P, rejected_trips, vehicle_request_assign)

