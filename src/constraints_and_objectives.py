import logging
logger = logging.getLogger(__name__)


def variables_declaration(K, P):
    # K : set of vehicles
    # P : set of customers to serve
    # binary represent if the customer i is picked immediately after j by a taxi
    # initialized with False
    X = {i.id: {j.id: False for j in P} for i in P}

    # binary represent if the customer i is picked up by vehicle k as a first customer
    # initialized with False
    Y = {k.id: {i.id: False for i in P} for k in K}

    # pick up time for customers
    # initialized with 0
    U = {i.id: 0 for i in P}

    # binary represent if the customer i is selected to be served
    # initialized with False
    Z = {i.id: False for i in P}

    return X, Y, U, Z


def verify_const_1(X, Y, Z, K, P):
    """ Function to verify the validation of the Constraint (1)
    K : set of vehicles
    P : set of customers to serve
    X , Y, Z : Model variables
    """

    verified = True

    for f_i in P:
        sum_x = 0
        sum_y = 0
        for f_j in P:
            sum_x += (1 if X[f_j.id][f_i.id] else 0)

        for f_k in K:
            sum_y += (1 if Y[f_k.id][f_i.id] else 0)

        z_i = 1 if Z[f_i.id] else 0
        if z_i != sum_x + sum_y:
            verified = False
            break

    return verified


def verify_const_2(X, Z, P):
    """ Function to verify the validation of the Constraint (2)
        K : set of vehicles
        P : set of customers to serve
        X , Z : Model variables
    """

    verified = True

    for f_i in P:
        sum_x = 0
        for f_j in P:
            sum_x += (1 if X[f_i.id][f_j.id] else 0)

        z_i = 1 if Z[f_i.id] else 0
        if z_i < sum_x:
            verified = False
            break

    return verified


def verify_const_3(Y, K, P):
    """ Function to verify the validation of the Constraint (3)
        K : set of vehicles
        P : set of customers to serve
        Y : Model variables
    """
    verified = True

    for f_k in K:
        sum_y = 0
        for f_i in P:
            sum_y += (1 if Y[f_k.id][f_i.id] else 0)

        if sum_y > 1:
            verified = False
            break

    return verified


def verify_const_4(U, P):
    """ Function to verify the validation of the Constraint (4)
        P : set of customers to serve
        U : Model variables
    """

    verified = True
    for f_i in P:
        ready_time_f_i = f_i.ready_time
        latest_time_f_i = f_i.latest_pickup
        if U[f_i.id] < ready_time_f_i or U[f_i.id] > latest_time_f_i:
            verified = False
            break

    return verified


def verify_const_5(X, U, P, durations):
    """ Function to verify the validation of the Constraint (5)
        P : set of customers to serve
        X , U : Model variables
    """
    verified = True
    for f_i in P:
        for f_j in P:
            if f_i != f_j:
                T_ij = f_i.shortest_travel_time + durations[f_i.destination.label][f_j.origin.label]
                if (U[f_j.id] - U[f_i.id]).__round__(3) < (
                        T_ij if X[f_i.id][f_j.id] else (f_j.ready_time - f_i.latest_pickup)).__round__(3):
                    verified = False
                    break
        if not verified:
            break

    return verified


def verify_const_6(Y, U, P, K, vehicle_request_assign, durations):
    """ Function to verify the validation of the Constraint (6)
        K : set of vehicles
        P : set of customers to serve
        Y , U : Model variables
    """
    verified = True
    for f_i in P:
        for f_k in K:
            T_ki = durations[vehicle_request_assign[f_k.id]['departure_stop']][f_i.origin.label]
            if U[f_i.id].__round__(3) < ((vehicle_request_assign[f_k.id]['departure_time'] + T_ki) if Y[f_k.id][f_i.id] else f_i.ready_time).__round__(3):
                verified = False
                break
        if not verified:
            break

    return verified


def verify_all_constraints(X, Y, U, Z, K, P, vehicle_request_assign, durations):
    """ Function to verify all Constraints"""

    return verify_const_1(X, Y, Z, K, P) and \
        verify_const_2(X, Z, P) and \
        verify_const_3(Y, K, P) and \
        verify_const_4(U, P) and \
        verify_const_5(X, U, P, durations) and \
        verify_const_6(Y, U, P, K, vehicle_request_assign, durations)


def calc_obj_total_customers(Z, P):
    """ Function to calculate the total number of served customers
        P : set of customers to serve
        C : Model variables
    """

    value = 0
    for f_i in P:
        value += (1 if Z[f_i.id] else 0)

    return value



