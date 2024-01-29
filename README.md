# Realtime Taxi routing Overview

The Taxi routing System is a solution designed to simulate and optimize taxi dispatching operations. This project requires thee `multimodalsim` package for simulation and optimization of multimodal transportation systems. 

## Modules

- **data_reader.py**: Handles input data reading and preprocessing.
- **RideRequest.py**: Defines the `RideRequest` class and associated methods.
- **utilities.py**: Provides utility functions used across the system.
- - **taxi_dispatcher.py**: Core module where the dispatching logic and algorithms are implemented.
- **Offline_solver.py**: Contains the logic for solving dispatch scenarios in offline mode, when all the requests are known in advance.
- **run_simulation.py**: Facilitates running simulations of the taxi dispatching system under various conditions.
- - **Run_Example.py**: An example script demonstrating how to run a basic instance of the dispatch system.
- **Run_Tests.py**: Executes a series of tests to validate the correctness and performance of the system.


## multimodalsim Package Overview

The `multimodalsim` package is a Python library for simulating multi-modal discrete event transportation systems, focusing on the dynamics between trips (passengers) and vehicles within a network. It enables the comprehensive setup, execution, and analysis of simulations to evaluate transportation strategies.

### Setup
To install the package, ensure that Python is installed on your system. Clone the repository or download the source code, open a terminal in the `multimodal-simulator` directory and execute the following command:

    python setup.py install

### Key Components
- **Agents**: Simulates two primary agents: trips (passengers) and vehicles. Trips are modeled as `Trip` objects with detailed attributes, including origin, destination, and timing constraints. Vehicles modeled as `Vehicle` objects, transport passengers based on the simulation's dynamics.

- **Environment**: The simulation environment where all agents operate, and events are processed.

- **Events**: Fundamental units driving the simulation's progress. Events are categorized into optimization, passenger, and vehicle events. The handling of events follows a priority queue mechanism, ensuring timely and orderly processing.

### Simulation Flow
The simulation process is categorized into three main phases: Data Preparation, Initialization of Simulation Components, and Execution of the Simulation.

### 1. Read and Prepare Data
This phase involves reading input data, visualizing the network, and preparing vehicles and trips for the simulation.

- **Data Reading**:
  - Utilize a `TaxiDataReader` to read in taxi requests, vehicle information, and the network graph.
    ```python
    data_reader = TaxiDataReader(requests_file_path, vehicles_file_path, graph_file_path, vehicles_end_time=100000)
    vehicles, routes_by_vehicle_id = data_reader.get_json_vehicles()
    trips = data_reader.get_json_trips(solution_mode, time_window)
    ```

- **Network Visualization**:
  - Extract and draw the network graph for a visual representation of the network's structure.
    ```python
    network_graph = data_reader.get_json_graph()
    ut.draw_network(network_graph, graph_file_path)
    ```
    
### 2. Initialize Simulation Components
Set up the core components of the simulation, including the dispatcher, optimization model, and environment observer. Insidee Dispatcher class there are three main methods for prearing inputs, optimizing and creating route plans.

- **Dispatcher Setup**:
  - Initialize a `TaxiDispatcher` with the network graph, chosen algorithm, and objective.
    ```python
    dispatcher = TaxiDispatcher(network_graph, algorithm, objective)
    ```

- **Optimization Setup**:
  - Create an `Optimization` object with the dispatcher to manage trip splitting and route assignment.
    ```python
    opt = Optimization(dispatcher)
    ```

- **Environment Observer**:
  - Initialize a `StandardEnvironmentObserver` for simulation monitoring and visualization.
    ```python
    environment_observer = StandardEnvironmentObserver()
    ```

### 3. Initialize and Run the Simulation
Set up the simulation with all components and execute it.

- **Simulation Initialization**:
  - Create a `Simulation` object with the optimization model, trips, vehicles, routes, network graph, and environment observer. 
    ```python
    simulation = Simulation(opt, trips, vehicles, routes_by_vehicle_id, network=network_graph, environment_observer=environment_observer)
    ```

- **Simulation Execution**:
  - Start the simulation process by calling the `simulate` method, managing the state and utilizing the environment observer.
    ```python
    simulation.simulate()
    ```
