import networkx as nx
import matplotlib.pyplot as plt
from enum import Enum


class Objectives(Enum):
    """ objective functions:
        - total_Profit: total profit of served requests
        - waiting_time: total wait time of served requests
        - total_customers: total number of served customers
    """
    PROFIT = "total_profit"
    TOTAL_CUSTOMERS = "total_customers"
    WAIT_TIME = "waiting_time"


class SolutionMode(Enum):
    """ solution modes:
        - offline : all the requests revealed at the start (release time = 0 for all requests)
        - fully_online : release time is equal to the ready time for all requests
        - online : requests are known 30 minutes before the ready time
        - partial : a part of requests are known at the start and for the rest release time is equal to the ready time
    """
    OFFLINE = "offline"
    ONLINE = "online"
    FULLY_ONLINE = "fully_online"
    PARTIAL = "partially_known"


class Algorithm(Enum):
    """ Algorithm used to optimize the plan:
        - MIP_SOLVER : using the Gurobi MIP solver to solve the problem
        - GREEDY : greedy approach to assign arrival requests to vehicles
        - RANDOM : random algorithm to assign arrival requests to vehicles
        - RANKING : ranking method to assign arrival requests to vehicles
        - QUALITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            a counter is incremented for the best request to assign at each scenario.
        - QUANTITATIVE_CONSENSUS : consensus online stochastic algorithm to assign arrival requests to vehicles
            the best request to assign is credited by the optimal solution value, rather than merely incrementing a counter.
        - RE_OPTIMIZE: Algorithm to re-optimize the solution based on destroy and repair
    """
    MIP_SOLVER = "MIP_SOLVER"
    GREEDY = "GREEDY"
    RANDOM = "RANDOM"
    RANKING = "RANKING"
    QUALITATIVE_CONSENSUS = "QUALITATIVE_CONSENSUS"
    QUANTITATIVE_CONSENSUS = "QUANTITATIVE_CONSENSUS"
    RE_OPTIMIZE = "RE_OPTIMIZE"


class DestroyMethod(Enum):
    """ Method used for destruction in RE_OPTIMIZE algorithm
        - DEFAULT: Default destruction method (Complete re-optimization)
        - FIX_VARIABLES: fix some of the variables in the model
        - FIX_ARRIVALS: fix a time window around the arrival time
        - BONUS: arbitrary destroy method as bonus
    """
    DEFAULT = "default"
    FIX_ARRIVALS = "fix_arrivals"
    FIX_VARIABLES = "fix_variables"
    BONUS = "bonus"



def get_distances(G):
    """ Function: calculate the shortest distance between each pair of stop nodes in the network graph
        G : routing network graph
    """
    distances = {}
    for node1, data in G.nodes(data=True):
        if node1 not in distances:
            distances[node1] = {}
        for node2 in G.nodes():
            distances[node1][node2] = data['shortest_paths'][node2]['total_distance']

    return distances


def get_durations(G):
    """ Function: calculate the shortest travel time between each pair of stop nodes in the network graph
        G : routing network graph
    """
    durations = {}
    for node1, data in G.nodes(data=True):
        if node1 not in durations:
            durations[node1] = {}
        for node2 in G.nodes():
            durations[node1][node2] = data['shortest_paths'][node2]['total_duration']

    return durations


def get_costs(G):
    """ Function: calculate the cost of driving between each pair of stop nodes in the network graph
        here the cost is $5 per hour of driving
        G : routing network graph
    """
    costs = {}
    for node1, data in G.nodes(data=True):
        if node1 not in costs:
            costs[node1] = {}
        for node2 in G.nodes():
            costs[node1][node2] = data['shortest_paths'][node2]['total_duration'] / 3600 * 5
    return costs


def print_dict_as_table(input_dict):
    """Function: print a dictionary in a tabular format
    """
    # Find the maximum length of the keys for formatting
    max_key_length = max(len(str(key)) for key in input_dict.keys())
    max_value_length = max(len(str(value)) for value in input_dict.values())

    header_key = "Attribute"
    header_value = "Value"
    max_key_length = max(max_key_length, len(header_key))
    max_value_length = max(max_value_length, len(header_value))

    # Print table headers
    print(f"{header_key}{' ' * (max_key_length - len(header_key) + 2)} | {header_value}")
    print("-" * (max_key_length + 2) + "+" + "-" * (max_value_length + 2))

    # Print each item in the dictionary
    for key, value in input_dict.items():
        # Adjust spacing based on key and value length
        key_spacing = " " * (max_key_length - len(str(key)) + 2)
        print(f"{key}{key_spacing} | {value}")


def draw_network(network, save_path):
    """Function : Draw the network graph.
    """
    plt.figure(figsize=(12, 12))

    # Extract positions from node attributes
    pos = {node: (data['Node']['coordinates'][0], data['Node']['coordinates'][1]) for node, data in
           network.nodes(data=True)}

    nx.draw_networkx(
        network,
        pos=pos,
        with_labels=True,
        node_size=70,
        width=1,
        font_size=6,
        node_color='yellowgreen',
        edge_color='gray',
        arrows=True
    )

    # Add edge labels for edges with length > 800
    labels = {(u, v): attrs['length'] for (u, v, attrs) in network.edges(data=True) if
              attrs['length'] > 800}
    nx.draw_networkx_edge_labels(network, pos=pos, edge_labels=labels, font_size=7)

    # Save the figure
    plt.savefig(save_path + '/Network.png', dpi=1000)
    plt.close()
