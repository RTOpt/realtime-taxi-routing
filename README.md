# Realtime Taxi routing Overview

The Taxi routing System is a solution designed to simulate and optimize taxi dispatching operations. This project requires the `multimodalsim` package for simulation and optimization of multimodal transportation systems. 

## Modules

- **data_reader.py**: Handles input data reading and preprocessing.
- **RideRequest.py**: Defines the `RideRequest` class and associated methods.
- **utilities.py**: Provides utility functions used across the system.
- **taxi_dispatcher.py**: Core module where the dispatching logic and algorithms are implemented.
- **Offline_solver.py**: Contains the logic for solving dispatch scenarios in offline mode, when all the requests are known in advance.
- **run_simulation.py**: Facilitates running simulations of the taxi dispatching system under various conditions.
- **Run_Example.py**: An example script demonstrating how to run a basic instance of the dispatch system.
- **Run_Tests.py**: Executes a series of tests to validate the correctness and performance of the system.


## multimodalsim Package Overview

The `multimodalsim` package is a Python library for simulating multi-modal discrete event transportation systems, focusing on the dynamics between trips (passengers) and vehicles within a network. It enables the comprehensive setup, execution, and analysis of simulations to evaluate transportation strategies.

### Key Components
- **Agents**: Simulates two primary agents: trips (passengers) and vehicles. Trips are modeled as `Trip` objects with detailed attributes, including origin, destination, and timing constraints. Vehicles modeled as `Vehicle` objects, transport passengers based on the simulation's dynamics.

- **Environment**: The simulation environment where all agents operate, and events are processed.

- **Events**: Fundamental units driving the simulation's progress. Events are categorized into optimization, passenger, and vehicle events. The handling of events follows a priority queue mechanism, ensuring timely and orderly processing.

### Simulation Flow
The simulation process is categorized into three main phases: Data Preparation, Initialization of Simulation Components, and Execution of the Simulation.

### 1. Read and Prepare Data
This phase involves reading input data, visualizing the network, and preparing vehicles and trips for the simulation.

- **Data Reading**:
  Utilize a `TaxiDataReader` to read in taxi requests, vehicle information, and the network graph.
    ```python
    data_reader = TaxiDataReader(requests_file_path, vehicles_file_path, graph_file_path, vehicles_end_time=100000)
    vehicles, routes_by_vehicle_id = data_reader.get_json_vehicles()
    trips = data_reader.get_json_trips(solution_mode, time_window)
    ```

- **Network Visualization**:
  Extract and draw the network graph for a visual representation of the network's structure.
    ```python
    network_graph = data_reader.get_json_graph()
    draw_network(network_graph, graph_file_path)
    ```
    
### 2. Initialize Simulation Components
Set up the core components of the simulation, including the dispatcher, optimization model, and environment observer. Insidee Dispatcher class there are three main methods for prearing inputs, optimizing and creating route plans.

- **Dispatcher Setup**:
  Initialize a `TaxiDispatcher` with the network graph, chosen algorithm, and objective.
    ```python
    dispatcher = TaxiDispatcher(network_graph, algorithm, objective)
    ```

- **Optimization Setup**:
  Create an `Optimization` object with the dispatcher to manage trip splitting and route assignment.
    ```python
    opt = Optimization(dispatcher)
    ```

- **Environment Observer**:
  Initialize a `StandardEnvironmentObserver` for simulation monitoring and visualization.
    ```python
    environment_observer = StandardEnvironmentObserver()
    ```

### 3. Initialize and Run the Simulation
Set up the simulation with all components and execute it.

- **Simulation Initialization**:
  Create a `Simulation` object with the optimization model, trips, vehicles, routes, network graph, and environment observer. 
    ```python
    simulation = Simulation(opt, trips, vehicles, routes_by_vehicle_id, network=network_graph, environment_observer=environment_observer)
    ```

- **Simulation Execution**:
  Start the simulation process by calling the `simulate` method, managing the state and utilizing the environment observer.
    ```python
    simulation.simulate()
    ```

# Installation and Setup

## Prerequisites
- Python 3.x: The system is developed and tested with Python 3.x. Ensure you have it installed on your system. You can download it from [the official Python website](https://www.python.org/).

## Setting Up the Environment
1. **Clone the Repository**: Start by cloning the repository to your local machine. Use the following command:
   ```bash
   git clone https://github.com/RTOpt/realtime-taxi-routing.git

2. **Create a Virtual Environment (Optional but Recommended)**:
It's a best practice to create a virtual environment for your project to avoid conflicts with system-wide Python packages. Use the following commands to navigate to the project directory and create the environment. Replace [project-directory] with the address of the place you have saved the project.
    ```bash
    cd [project-directory]/realtime-taxi-routing
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   
3. **Instal `Setuptools` package**: Install `Setuptools` package if it is not installed on your system:
    ```bash
    pip install --upgrade pip
    pip install setuptools
   
4. **Installing the `multimodalsim` Package**: Execute the following commands to navigate to the package directory and install the package and requited dependencies:
    ```bash
    cd multimodal-simulator/python
    python setup.py install
5. **Using the Virtual Environment as the Python Interpreter**: After setting up the virtual environment.

#### PyCharm:
1. Open your project in PyCharm.
2. Go to `File` > `Settings`.
3. Navigate to `Project: your-project-name` > `Python Interpreter`.
4. Click on `Add Interpreter`, and choose the Python interpreter located in your virtual environment (typically under the `venv/bin/python` path).

#### Visual Studio Code:
1. Open your project folder in VS Code.
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) to open the command palette.
3. Type `Python: Select Interpreter` and select the command.
4. Choose the interpreter from your virtual environment (usually found in the `.venv` or `venv` folder).


## Installing Gurobi and Obtaining a Student License

Gurobi is an optimization solver used in various industries and academic research. Follow the steps below to install Gurobi and obtain a student license:

1. **Register and Download Gurobi**:
   - Visit the [Gurobi Download Center](https://www.gurobi.com/downloads/gurobi-software/).
   - Register for an account if you don't already have one. Ensure you use your academic email address to qualify for the free academic license.
   - Download the appropriate version of Gurobi for your operating system.

2. **Install Gurobi**:
   - Follow the [Software Installation Guide](https://support.gurobi.com/hc/en-us/articles/14799677517585) specific to your operating system to install Gurobi.

3. **Obtain a Free Academic License**:
   - Visit the [Gurobi License Center](https://www.gurobi.com/downloads/end-user-license-agreement-academic/).
   - Apply for a free academic license. You will need to provide your university email address and verify your academic status.
   - Follow the instructions to activate your license. Typically, this involves running a command in your terminal or command prompt.

4. **Set Up the Gurobi Environment**:
   - Ensure that your Python environment is set up to recognize Gurobi. If you're using a virtual environment for your project, you may need to update it with Gurobi's Python bindings.
   ```bash
    python -m pip install gurobipy

For the most up-to-date and detailed installation instructions, please refer to the [official Gurobi documentation](https://www.gurobi.com/documentation/).

**Note**: The process for obtaining a Gurobi license may change, and the terms of use for Gurobi software are subject to Gurobi's licensing agreement. Ensure you comply with all license terms and conditions.