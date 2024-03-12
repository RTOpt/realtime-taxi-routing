from random import randint

import numpy as np
import networkx as nx
from scipy.stats import expon
from src.RideRequest import RideRequest
from multimodalsim.simulator.vehicle import LabelLocation, Stop, Vehicle
from src.utilities import SolutionMode


def create_random_requests(network, cust_node_hour, start_ID, start_time, durations, solution_mode=SolutionMode.OFFLINE,
                           sim_time=3600, hour_fare=80.,
                           time_window=5 * 60, cust_call=30 * 60, nb_requests=None):
    """ Function: adds random customers based on cust_node_hour rate
        Input:
        ------------
            network : The road network, including nodes representing stop points.
            cust_node_hour : customers are a Poisson process for each node with a mean of `cust_node_hour`
                customers per node per hour
            start_ID : Starting ID for the generated trip requests.
            start_time: The time in seconds after which requests are received
            durations : A nested dictionary containing travel times between nodes, with outer keys as origin node IDs
                and inner keys as destination node IDs.
            sim_time: The total time in seconds for receiving requests. Defaults to 3600 (1 hour).
            hour_fare: fare paid for serving request. Defaults to 80$.
            time_window: The time window in seconds within which customers are willing to be picked up after their
                ready time. Defaults to 5 minutes (300 seconds).
            cust_call: The time in seconds before the ready time that customers call to make a request.
                Defaults to 30 minutes (1800 seconds).
            nb_requests: Maximum number of requests to generate.
            solution_mode: The mode of solution (helps in determining the release time)

        Output:
        ------------
            trips: List of generated requests
    """
    id = start_ID
    trips = []
    waitTime = expon(scale=3600. / (cust_node_hour * len(network.nodes)))
    t = start_time + waitTime.rvs()
    while t <= start_time + sim_time:
        orig_id = np.random.randint(0, len(network.nodes))
        dest_id = np.random.randint(0, len(network.nodes) - 1)
        if orig_id == dest_id:
            dest_id += 1

        lon_orig = lat_orig = None
        lon_dest = lat_dest = None

        orig_location = LabelLocation(str(orig_id), lon=lon_orig, lat=lat_orig)
        dest_location = LabelLocation(str(dest_id), lon=lon_dest, lat=lat_dest)
        # calculate fare based on time
        fare_value = (hour_fare / 3600) * durations[str(orig_id)][str(dest_id)]

        t_ready = t.__round__(3)
        if solution_mode == SolutionMode.OFFLINE:
            t_release = start_time
        elif solution_mode == SolutionMode.FULLY_ONLINE:
            t_release = t_ready
        else:
            t_release = max(0., t_ready - cust_call)

        nb_passengers = randint(1, 3)
        trip = RideRequest(str(int(id)),
                           orig_location,
                           dest_location,
                           nb_passengers,
                           release_time=t_release,
                           ready_time=t_ready,
                           due_time=100000,
                           latest_pickup=(t_ready + time_window * 60).__round__(3),
                           fare=fare_value.__round__(3),
                           shortest_travel_time=durations[str(orig_id)][str(dest_id)])
        id += 1
        trips.append(trip)
        t += waitTime.rvs()
        if nb_requests is not None and len(trips) < nb_requests:
            break
    return trips


def add_random_vehicles(network, start_ID, nb_vehicles, start_time=0, vehicles_end_time=100000, boarding_time=10,
                        capacity=4):
    """ Function: adds random taxis (uniformly) to the system
        Input:
        ------------
            network : The road network, including nodes representing stop points.
            nb_Taxi : the number of taxis that are added with uniform initial positions and 0 initial time
            start_ID : Starting ID for the taxi
            start_time: The time in seconds after which vehicles are available
            vehicles_end_time: The time in seconds after which vehicles are not available

        Output:
        ------------
            taxis: List of generated requests
    """
    id = start_ID
    vehicles = []
    for i in range(nb_vehicles):
        vehicle_id = str(int(id))

        stop_departure_time = start_time + boarding_time
        stop_id = str(np.random.randint(0, len(network.nodes)))

        lon, lat, mode = None, None, None
        start_stop_location = LabelLocation(stop_id, lon=lon, lat=lat)

        start_stop = Stop(start_time,
                          stop_departure_time,
                          start_stop_location)

        # Create and append Vehicle object
        vehicle = Vehicle(vehicle_id, start_time, start_stop, capacity,
                          start_time, vehicles_end_time,
                          mode=mode, reusable=True)
        id += 1
        vehicles.append(vehicle)
    return vehicles


import json


def save_trips_to_json(trips, save_file_path):
    """ Function: save list of requests in a json file
        Input:
        ------------
            trips: List of trip objects or dictionaries.
            save_file_path: String specifying the path to the output JSON file.
    """
    # Convert trip objects to dictionaries
    trips_data = []
    for trip in trips:
        trip_dict = {
            "id": trip.id,
            "orig": trip.origin.label,
            "dest": trip.destination.label,
            "tcall": trip.release_time,
            "tmin": trip.ready_time,
            "tmax": trip.latest_pickup,
            "fare": trip.fare
        }
        trips_data.append(trip_dict)

    # Save the list of dictionaries to a JSON file
    with open(save_file_path, 'w') as f:
        json.dump(trips_data, f, indent=4)


def save_vehicles_to_json(vehicles, save_file_path):
    """ Function: save list of vehicles in a json file
        Input:
        ------------
            trips: List of trip objects or dictionaries.
            save_file_path: String specifying the path to the output JSON file.
    """
    # Convert trip objects to dictionaries
    vehicle_data = []
    for vehicle in vehicles:
        vehicle_dict = {
            "id": vehicle.id,
            "initPos": vehicle.start_stop.location.label,
            "initTime": vehicle.start_time,
        }
        vehicle_data.append(vehicle_dict)

    # Save the list of dictionaries to a JSON file
    with open(save_file_path, 'w') as f:
        json.dump(vehicle_data, f, indent=4)
