from multimodalsim.simulator.request import Trip


class RideRequest(Trip):
    """
    RideRequest extends the Trip class with additional attributes specific to ride requests.
        Additional Attributes:
        ----------------------
        fare: float
           fare paid for serving request.
        latest_pickup: float
           The latest possible time for passenger pickup.
        shortest_travel_time: float
           travel time between its origin and destination
    """

    def __init__(self, id, origin, destination, nb_passengers, release_time,
                 ready_time, due_time, name=None, latest_pickup=None, fare=None, shortest_travel_time=None):
        # Call the constructor of the parent class (Request)
        super().__init__(id, origin, destination, nb_passengers, release_time,
                         ready_time, due_time, name)
        # Add the additional attribute
        self.__fare = fare
        self.__shortest_travel_time = shortest_travel_time
        self.__latest_pickup = latest_pickup




    @property
    def latest_pickup(self):
        """Getter for the latest_pickup attribute."""
        return self.__latest_pickup

    @property
    def fare(self):
        """Getter for the fare attribute."""
        return self.__fare


    @property
    def shortest_travel_time(self):
        """Getter for the shortest_travel_time attribute."""
        return self.__shortest_travel_time


    @latest_pickup.setter
    def latest_pickup(self, latest_pickup):
        """Setter for the latest_pickup_time attribute."""
        self.__latest_pickup = latest_pickup



