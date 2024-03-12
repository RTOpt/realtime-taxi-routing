from multimodalsim.reader.data_reader import DataReader
from src.RideRequest import RideRequest
from multimodalsim.simulator.vehicle import LabelLocation, Stop, Vehicle
import json
import networkx as nx
from src.utilities import SolutionMode
import pickle
import random





class TaxiDataReader(DataReader):
    """
    TaxiDataReader is responsible for reading and processing input data from files,
    including trip requests, vehicle information, and the transportation network.

    Additional Attributes:
    ------------
    requests_json_file_path : str
        File path to the JSON file containing trip requests.
    vehicles_json_file_path : str
        File path to the JSON file containing vehicle data.
    graph_from_json_file_path : str
        File path to the JSON file containing the transportation network graph.
    sim_end_time : int
        Simulation end time.
    vehicles_end_time : int
        End time for vehicles' operations.
    """
    def __init__(self, requests_json_file_path, vehicles_json_file_path,
                 graph_from_json_file_path=None, sim_end_time=None,
                 vehicles_end_time=None):
        # Call the constructor of the parent class (DataReader)
        super().__init__()
        self.__network = None
        self.requests_json_file_path = requests_json_file_path
        self.vehicles_json_file_path = vehicles_json_file_path
        self.__graph_from_json_file_path = graph_from_json_file_path

        # The time difference between the arrival and the departure time.
        self.__boarding_time = 10
        self.__sim_end_time = sim_end_time
        self.__vehicles_end_time = vehicles_end_time

    def get_json_trips(self, solution_mode, time_window, known_portion=0):
        """ Function: read trip from a file
            Input:
            ------------
            solution_mode : The mode of solution (offline, fully online, etc.).
            time_window : Time window for requests pickup
            known_portion: portion of requests that are known in advance

            Output:
            ------------
            trips : A list of RideRequest objects.
        """
        trips = []
        with open(self.requests_json_file_path) as f:
            js_data = json.load(f)
            nb_passengers = 1  # Each request corresponds to 1 passenger.
            # Shuffle the indices and select known_portion of them
            indices = list(range(len(js_data)))
            random.shuffle(indices)
            known_trip_indices = indices[:int(len(js_data) * known_portion)]
            for idx, entry in enumerate(js_data):
                # Process trip data
                orig_id = str(int(entry['orig']) - 1)
                dest_id = str(int(entry['dest']) - 1)
                fare_value = float(entry['fare'])

                lon_orig = lat_orig = None
                lon_dest = lat_dest = None

                orig_location = LabelLocation(orig_id, lon=lon_orig, lat=lat_orig)
                dest_location = LabelLocation(dest_id, lon=lon_dest, lat=lat_dest)
                travel_time = None
                if self.__network is not None:
                    path_info = self.__network.nodes[orig_id]['shortest_paths'][dest_id]
                    travel_time = path_info['total_duration']
                if solution_mode == SolutionMode.OFFLINE:
                    release_time = 0
                elif solution_mode == SolutionMode.FULLY_ONLINE:
                    release_time = entry['tmin'].__round__(3)
                elif solution_mode == SolutionMode.PARTIAL:
                    # Check if the current trip index is in the known_trip_indices
                    if idx in known_trip_indices:
                        release_time = 0
                    else:
                        release_time = entry['tmin'].__round__(3)
                else:
                    release_time = entry['tcall'].__round__(3)

                # Create and append RideRequest object
                trip = RideRequest(str(int(entry['id']) - 1),
                                   orig_location,
                                   dest_location,
                                   nb_passengers,
                                   release_time=release_time,
                                   ready_time=entry['tmin'].__round__(3),
                                   due_time=100000,
                                   latest_pickup= (entry['tmin'] + time_window * 60).__round__(3),
 #                                  latest_pickup=entry['tmax'].__round__(3),
                                   fare=fare_value,
                                   shortest_travel_time=travel_time)
                trips.append(trip)
        return trips

    def get_json_vehicles(self):
        """ Function: read vehicles from a file
                Output:
                ------------
                vehicles: a list of Vehicle objects
                routes_by_vehicle_id : a dictionary of routes by vehicle ID
        """
        vehicles = []
        routes_by_vehicle_id = {}  # Remains empty

        with open(self.vehicles_json_file_path) as f:
            js_data = json.load(f)
            for entry in js_data:
                # Process vehicle data
                vehicle_id = str(int(entry['id']) - 1)
                start_time = float(entry['initTime'])
                stop_departure_time = start_time + self.__boarding_time
                capacity = 4
                stop_id = str(int(entry['initPos']) - 1)

                lon, lat, mode = None, None, None
                start_stop_location = LabelLocation(stop_id, lon=lon, lat=lat)

                start_stop = Stop(start_time,
                                  stop_departure_time,
                                  start_stop_location)

                # reusable=True since the vehicles are shuttles.
                # Create and append Vehicle object
                vehicle = Vehicle(vehicle_id, start_time, start_stop, capacity,
                                  start_time, self.__vehicles_end_time,
                                  mode=mode, reusable=True)

                vehicles.append(vehicle)

        return vehicles, routes_by_vehicle_id

    def get_json_graph(self):
        """ Function: read network from a json file
                Output:
                ------------
                network: routing network graph
        """
        with open(self.__graph_from_json_file_path) as f:
            data = json.load(f)
            nodes = data["network"]["nodes"]
            roads = data["network"]["roads"]
            costs = data["times"]

            self.__network = nx.DiGraph()
            pos = {}
            # Process nodes
            for i, node_data in enumerate(nodes):
                node_dict = {
                    "id": str(i),
                    "coordinates": [float(node_data["x"]), float(node_data["y"])],
                    "in_arcs": [],
                    "_out_arcs": []
                }
                pos[str(i)] = (float(node_data["x"]), float(node_data["y"]))
                self.__network.add_node(str(i), pos=[float(node_data["x"]), float(node_data["y"])], Node=node_dict)

            # Process edges
            precision = 3
            for road_key, road_data in roads.items():
                orig, dest = eval(road_key)
                length = round(float(road_data['distance']), precision)

                self.__network.add_edge(str(orig - 1), str(dest - 1),
                                        cost=round(float(costs[orig - 1][dest - 1]) / 3600 * 5, precision),
                                        duration=round(float(costs[orig - 1][dest - 1]), precision),
                                        length=length)

            self.find_shortest_paths()

        return self.__network

    def find_shortest_paths(self):
        """ Function: find the shortest path between each pair of stop locations in the network"""
        # Ensure the network is connected
        if not nx.is_weakly_connected(self.__network):
            raise ValueError("The network is not connected.")

        # Initialize the 'shortest_paths' attribute for nodes
        nx.set_node_attributes(self.__network, {}, 'shortest_paths')

        # Iterate over all pairs of nodes
        for source in self.__network.nodes:
            for target in self.__network.nodes:
                if source != target:
                    # Find the shortest path based on duration
                    shortest_path = nx.shortest_path(self.__network, source=source, target=target, weight='duration')

                    # Access the edges along the path
                    path_edges = [(shortest_path[i], shortest_path[i + 1]) for i in range(len(shortest_path) - 1)]

                    # Calculate and save the sum of 'duration', 'distance', and 'cost'
                    total_duration = sum(self.__network[edge[0]][edge[1]]['duration'] for edge in path_edges)
                    total_distance = sum(self.__network[edge[0]][edge[1]]['length'] for edge in path_edges)
                    total_cost = sum(self.__network[edge[0]][edge[1]]['cost'] for edge in path_edges)

                    # Save the information for the source node
                    source_node_data = self.__network.nodes[source]
                    if 'shortest_paths' not in source_node_data:
                        source_node_data['shortest_paths'] = {}
                    source_node_data['shortest_paths'][target] = {
                        'path_edges': path_edges,
                        'path_nodes': shortest_path,
                        'total_duration': total_duration,
                        'total_distance': total_distance,
                        'total_cost': total_cost
                    }
                else:
                    shortest_path = {}
                    path_edges = []

                    total_duration = 0
                    total_distance = 0
                    total_cost = 0

                    source_node_data = self.__network.nodes[source]
                    if 'shortest_paths' not in source_node_data:
                        source_node_data['shortest_paths'] = {}
                    source_node_data['shortest_paths'][target] = {
                        'path_edges': path_edges,
                        'path_nodes': shortest_path,
                        'total_duration': total_duration,
                        'total_distance': total_distance,
                        'total_cost': total_cost
                    }

    def save_graph(self, file_path):
        """Save the graph with all its data to a file."""
        with open(file_path + '/network.pkl', 'wb') as f:
            pickle.dump(self.__network, f)

        f.close()

    def load_graph(self, file_path):
        """Load the graph with all its data from a file."""
        with open(file_path, 'rb') as f:
            self.__network = pickle.load(f)
        f.close()
        return self.__network


