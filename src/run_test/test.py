import json
import math
import os
import pickle
from typing import Any, Dict
import networkx as nx
import numpy as np
import pandas as pd
from multimodalsim.simulator.vehicle import Vehicle
from multimodalsim.simulator.stop import LabelLocation, Stop
import random

from src.utilities.create_scenario import create_random_requests
from src.utilities.tools import find_shortest_paths, draw_network, get_durations, determine_cust_node_hour, \
    print_dict_as_table

BASE_FOLDER = "data/Instances"
GRAPH_FILE_PATH = os.path.join(BASE_FOLDER, "network.json")



def generate_urban_network(num_suburbs: int = 8, city_num_nodes: int = 64, suburb_num_nodes: int = 16,
                           block_distance: float = 800.0) -> nx.DiGraph:
    """
    Generates an urban-like network with a main city and surrounding suburbs with random shapes.

    Parameters
    ----------
    num_suburbs : int
        Number of suburb areas to generate around the city.
    city_num_nodes : int
        Number of nodes in the main city.
    suburb_num_nodes : int
        Number of nodes in each suburb.
    block_distance : float, optional
        Distance parameter influencing node placement, by default 800.0 meters.

    Returns
    -------
    nx.DiGraph
        The generated transportation network graph with nodes and edges.
    """

    G = nx.DiGraph()

    # Create main city nodes with random positions within a circular area
    city_nodes = city_num_nodes
    city_radius = (block_distance * math.sqrt(city_num_nodes)) / math.pi  # Adjusted for area

    for node_id in range(city_num_nodes):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, city_radius)
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        node_id_str = str(node_id)
        node_dict = {
            "id": node_id_str,
            "coordinates": [x, y],
            "in_arcs": [],
            "out_arcs": []
        }
        G.add_node(node_id_str, pos=(x, y), Node=node_dict)

    # Place suburbs around the city in a circular pattern with random shapes
    angle_step = (2 * math.pi / num_suburbs) if num_suburbs > 0 else 0
    suburb_radius = block_distance * math.sqrt(suburb_num_nodes) / math.pi  # Adjusted for area

    for c in range(num_suburbs):
        angle = c * angle_step + random.uniform(-0.1, 0.1)  # Slight random rotation
        # Center of this suburb:
        cx = (city_radius + suburb_radius) * 1.2 * math.cos(angle)
        cy = (city_radius + suburb_radius) * 1.2 * math.sin(angle)

        for i in range(suburb_num_nodes):
            ang = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, suburb_radius)
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            node_id = city_num_nodes + c * suburb_num_nodes + i
            node_id_str = str(node_id)
            node_dict = {
                "id": node_id_str,
                "coordinates": [x, y],
                "in_arcs": [],
                "out_arcs": []
            }
            G.add_node(node_id_str, pos=(x, y), Node=node_dict)

    # Function to add bidirectional roads between two nodes
    def add_bidirectional_road(u_id, v_id):
        u = str(u_id)
        v = str(v_id)
        ux, uy = G.nodes[u]['pos']
        vx, vy = G.nodes[v]['pos']
        length = round(math.sqrt((vx - ux) ** 2 + (vy - uy) ** 2), 3)
        speed = 13.89  # m/s (~50 km/h)
        duration = round(length / speed, 3)  # seconds
        cost = round((duration / 3600.0) * 5.0, 3)  # $5 per hour

        # Add edge from u to v
        G.add_edge(u, v, cost=cost, duration=duration, length=length)
        G.nodes[u]['Node']['out_arcs'].append(v)
        G.nodes[v]['Node']['in_arcs'].append(u)

        # Add edge from v to u
        G.add_edge(v, u, cost=cost, duration=duration, length=length)
        G.nodes[v]['Node']['out_arcs'].append(u)
        G.nodes[u]['Node']['in_arcs'].append(v)

    # Connect each node to its k-nearest neighbors to ensure network connectivity
    def connect_nearest_neighbors(G, k=4):
        nodes_positions = {node: G.nodes[node]['pos'] for node in G.nodes}
        for node, pos in nodes_positions.items():
            # Calculate distances to all other nodes
            distances = []
            for other_node, other_pos in nodes_positions.items():
                if other_node != node:
                    dist = math.sqrt((pos[0] - other_pos[0]) ** 2 + (pos[1] - other_pos[1]) ** 2)
                    distances.append((other_node, dist))
            # Sort by distance
            distances.sort(key=lambda x: x[1])
            # Connect to k-nearest neighbors
            for neighbor, _ in distances[:k]:
                add_bidirectional_road(int(node), int(neighbor))

    connect_nearest_neighbors(G, k=4)

    # Compute the shortest paths for the network
    find_shortest_paths(G)

    return G

# Generate the network with random-shaped city and suburbs
network = generate_urban_network(
    num_suburbs=8,
    city_num_nodes=64,
    suburb_num_nodes=16,
    block_distance=200)

# Draw the network (optional)
draw_network(network, os.path.dirname("data/Instances/network.json"))