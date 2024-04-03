import gurobipy as gp
from gurobipy import GRB
from src.utilities import Objectives

def create_model(K, P, durations, vehicle_request_assign):
    """ Function: create model to solve with Gurobi Solver
        Input:
        ------------
            K : set of vehicles
            P : set of customers to serve
            duration : travel time matrix between possible stop points
            vehicle_request_assign: dictionary containing vehicle-request assignments.

        Output:
        ------------
            model: The created Gurobi model for the taxi routing problem.
            Y_var, X_var, Z_var, U_var: Decision variables added to the model for solving the problem.
    """
    model = gp.Model("TaxiRoutingModel")

    # Add decision variables to the model
    X_var = {}  # Decision variable for trip connection between customers
    U_var = {}  # Decision variable for departure time from each customer location
    Z_var = {}  # Decision variable for whether a customer is served or not
    for f_i in P:
        U_var[f_i.id] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, obj=0, name=f'U_{f_i.id}')
        Z_var[f_i.id] = model.addVar(vtype=GRB.BINARY, obj=0, name=f'Z_{f_i.id}')
        for f_j in P:
            if f_i != f_j:
                X_var[f_i.id, f_j.id] = model.addVar(vtype=GRB.BINARY, name=f'X_{f_i.id}_{f_j.id}')

    Y_var = {}  # Decision variable for assigning customer to vehicle
    for f_i in P:
        for f_k in K:
            Y_var[f_k.id, f_i.id] = model.addVar(vtype=GRB.BINARY, name=f'Y_{f_k.id}_{f_i.id}')

    # Update the model to include the new variables
    model.update()

    """Set up constraints"""
    # Constraints 1
    for f_i in P:
        model.addConstr(
            Z_var[f_i.id] == sum(Y_var[f_k.id, f_i.id] for f_k in K) + sum(
                X_var[f_j.id, f_i.id] for f_j in P if f_i != f_j))

    # Constraints 2
    for f_i in P:
        model.addConstr(
            Z_var[f_i.id] >= sum(X_var[f_i.id, f_j.id] for f_j in P if f_i != f_j))

    # Constraints 3
    for f_k in K:
        model.addConstr(sum(Y_var[f_k.id, f_i.id] for f_i in P) <= 1)

    # Constraints 4
    for f_i in P:
        ready_time_f_i = f_i.ready_time
        latest_time_f_i = f_i.latest_pickup
        model.addConstr(U_var[f_i.id] >= ready_time_f_i)
        model.addConstr(U_var[f_i.id] <= latest_time_f_i)

    # Constraints 5
    for f_i in P:
        for f_j in P:
            if f_i != f_j:
                T_ij = f_i.shortest_travel_time + durations[f_i.destination.label][f_j.origin.label]
                model.addConstr(
                    U_var[f_j.id] - U_var[f_i.id] >= (f_j.ready_time - f_i.latest_pickup) + X_var[f_i.id, f_j.id] * (
                            T_ij - (f_j.ready_time - f_i.latest_pickup)))

    # Constraints 6
    for f_i in P:
        for f_k in K:
            T_ki = durations[vehicle_request_assign[f_k.id]['departure_stop']][f_i.origin.label]
            model.addConstr(U_var[f_i.id] >= f_i.ready_time + (
                    vehicle_request_assign[f_k.id]['departure_time'] + T_ki - f_i.ready_time) * Y_var[f_k.id, f_i.id])

    return model, Y_var, X_var, Z_var, U_var


def define_objective(objective, X_var, Y_var, U_var, Z_var, model, K, P, costs, vehicle_request_assign):
    if objective == Objectives.PROFIT:
        define_objective_total_profit(X_var, Y_var, model, K, P, costs, vehicle_request_assign)
    elif objective == Objectives.TOTAL_CUSTOMERS:
        define_objective_total_customers(Z_var, model, P)
    elif objective == Objectives.WAIT_TIME:
        define_objective_total_wait_time(U_var, Z_var, model, P)


def define_objective_total_customers(Z_var, model, P):
    """ Function: define objective of maximizing the total number of served customers and add it to the model
        Input:
        ------------
            P : set of customers to serve
            model : The Gurobi model to optimize.
            Z_var : Model variables
    """
    model.setObjective(
        sum(Z_var[f_i.id] for f_i in P),
        sense=GRB.MAXIMIZE
    )


def define_objective_total_profit(X_var, Y_var, model, K, P, costs, vehicle_request_assign):
    """ Function: define objective of maximizing the total profit and add it to the model
        Input:
        ------------
            K : set of vehicles
            P : set of customers to serve
            model : The Gurobi model to optimize.
            X_var, Y_var : Model variables
            costs: driving costs
            vehicle_request_assign: dictionary containing vehicle-request assignments.
    """
    raise NotImplementedError("Offline_solver.define_objective_total_profit() not implemented")
    model.setObjective(
        """you should write your objective here ..."""
    )


def define_objective_total_wait_time(U_var, Z_var, model, P):
    """ Function: define objective of minimizing the total wait time and add it to the model
        Input:
        ------------
            K : set of vehicles
            P : set of customers to serve
            model : The Gurobi model to optimize.
            U_var, Z_var : Model variables
    """
    raise NotImplementedError("Offline_solver.define_objective_total_wait_time() not implemented")
    model.setObjective(
        """you should write your objective here ..."""
    )


def solve_offline_model(model, P, K, Y_var, X_var, Z_var, rejected_trips, vehicle_request_assign):
    """Function: optimize the model with MIP solver and
                Retrieve the variable values
                convert solution to vehicle_request_assign dictionary which is required to determine the route plan
        Input:
        ------------
            model : The Gurobi model to optimize.
            K : set of vehicles
            P : set of customers to serve
            Y_var, X_var, Z_var : Decision variables used in the model.
            rejected_trips : List of trips that are rejected in the optimization process.
            vehicle_request_assign: dictionary containing vehicle-request assignments.

        Output:
        ------------
            model.objVal: The objective value of the optimized model

    """
    # Optimize the model
    model.optimize()

    # Check if the optimization was successful
    if model.status != GRB.OPTIMAL:
        print("Optimization did not converge to an optimal solution.")
        return

    assigned_requests = []

    # Extract the solution and populate the vehicle_request_assign and rejected_trips
    for f_k in K:
        for trip in P:
            if round(Y_var[f_k.id, trip.id].x):
                vehicle_request_assign[f_k.id]['assigned_requests'].append(trip)
                f_i = trip
                is_added = True
                while is_added:
                    is_added = False
                    for f_j in P:
                        if f_j != f_i:
                            if round(X_var[f_i.id, f_j.id].x):
                                vehicle_request_assign[f_k.id]['assigned_requests'].append(f_j)
                                f_i = f_j
                                is_added = True
                                break

    for trip in P:
        if not round(Z_var[trip.id].x):
            rejected_trips.append(trip)
        else:
            assigned_requests.append(trip)

    return model.objVal.__round__(3)
