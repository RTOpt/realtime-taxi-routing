import logging
import csv
import math

import requests
import polyline
import numpy as np
from ast import literal_eval

from multimodalsim.config.coordinates_osrm_config import CoordinatesOSRMConfig
from multimodalsim.simulator.vehicle import TimeCoordinatesLocation

logger = logging.getLogger(__name__)


class Coordinates:

    def __init__(self):
        pass

    def update_position(self, vehicle, route, time):
        raise NotImplementedError(
            'Coordinates.update_position not implemented')

    def update_polylines(self, route):
        raise NotImplementedError(
            'Coordinates.update_polylines not implemented')


class CoordinatesFromFile(Coordinates):
    def __init__(self, coordinates_file_path):
        super().__init__()
        self.__coordinates_file_path = coordinates_file_path
        self.__vehicle_positions_dict = {}
        self.__read_coordinates_from_file()

    def update_position(self, vehicle, route, time):

        time_positions = None
        if vehicle.id in self.__vehicle_positions_dict:
            time_positions = self.__vehicle_positions_dict[vehicle.id]

        current_position = None
        if time_positions is not None:
            for pos_time, position in time_positions.items():
                if pos_time > time:
                    break
                current_position = position
        elif route is not None \
                and route.current_stop is not None:
            # If no time_positions are available, use location of current_stop.
            current_position = route.current_stop.location
        elif route is not None \
                and len(route.previous_stops) > 0:
            # If current_stop is None, use location of the most recent
            # previous_stops.
            current_position = route.previous_stops[-1].location

        update_time_dict(current_position, vehicle.id, time,
                         self.__vehicle_positions_dict)

        return current_position

    def update_polylines(self, route):
        return None

    def __read_coordinates_from_file(self):
        with open(self.__coordinates_file_path, 'r') as coordinates_file:
            coordinates_reader = csv.reader(coordinates_file,
                                            delimiter=',')
            next(coordinates_reader, None)
            for coordinates_row in coordinates_reader:

                time = int(coordinates_row[1])
                lon = float(coordinates_row[2])
                lat = float(coordinates_row[3])
                time_coordinates = TimeCoordinatesLocation(time, lon, lat)

                vehicle_id_col = literal_eval(coordinates_row[0])
                vehicle_id_list = vehicle_id_col \
                    if type(vehicle_id_col) == list else [vehicle_id_col]

                for vehicle_id in vehicle_id_list:
                    if vehicle_id not in self.__vehicle_positions_dict:
                        self.__vehicle_positions_dict[vehicle_id] = {}

                    self.__vehicle_positions_dict[vehicle_id][time] = \
                        time_coordinates


class CoordinatesOSRM(Coordinates):
    def __init__(self, config=None):
        super().__init__()

        config = CoordinatesOSRMConfig() if config is None else config
        self.__osrm_url = config.url

    def update_position(self, vehicle, route, current_time):

        current_position = None

        if route.current_stop is not None:
            current_position = route.current_stop.location
        elif len(route.previous_stops) > 0 \
                and vehicle.polylines is not None:
            # Current position is between two stops
            stop1 = route.previous_stops[-1]
            stop2 = route.next_stops[0]
            stop_id = str(len(route.previous_stops) - 1)

            current_coordinates = self.__extract_coordinates_from_polyline(
                vehicle, current_time, stop1, stop2, stop_id)

            current_position = TimeCoordinatesLocation(current_time,
                                                       current_coordinates[0],
                                                       current_coordinates[1])

        return current_position

    def update_polylines(self, route):

        polylines = {}

        all_stops = []
        all_stops.extend(route.previous_stops)
        if route.current_stop is not None:
            all_stops.append(route.current_stop)
        all_stops.extend(route.next_stops)

        stop_coordinates = [(stop.location.lon, stop.location.lat)
                            for stop in all_stops]
        stop_ids = [stop.location.label for stop in all_stops]

        if len(stop_coordinates) > 2:
            coordinates_str_list = [str(coord[0]) + "," + str(coord[1])
                                    for coord in stop_coordinates]

            service_url = "route/v1/driving/"
            coord_url = ";".join(coordinates_str_list)
            args_url = "?annotations=true&overview=full"

            request_url = self.__osrm_url + service_url + coord_url + args_url

            response = requests.get(request_url)

            res = response.json()

            if res['code'] == 'Ok':
                polylines = \
                    self.__extract_polylines_from_response(res, stop_ids)
            else:
                logger.warning(request_url)
                logger.warning(res)
                polylines = {}
                for i in range(0, len(stop_ids) - 1):
                    coordinates = [stop_coordinates[i],
                                   stop_coordinates[i + 1]]
                    leg_polyline = polyline.encode(coordinates, geojson=True)
                    leg_durations_frac = [1.0]
                    polylines[str(i)] = (leg_polyline, leg_durations_frac)
                    # polylines[stop_ids[i]] = (leg_polyline, leg_durations_frac)

        else:
            polylines[str(0)] = ("", [])
            # polylines[stop_ids[0]] = ("", [])

        return polylines

    def __extract_coordinates_from_polyline(self, vehicle, current_time, stop1,
                                            stop2, stop_id):

        # stop_polyline_durations = vehicle.polylines[stop1.location.label]
        stop_polyline_durations = vehicle.polylines[stop_id]

        stop_coordinates = polyline.decode(stop_polyline_durations[0],
                                           geojson=True)
        stop_durations = stop_polyline_durations[1]

        time1 = stop1.departure_time
        time2 = stop2.arrival_time
        current_coordinates = \
            self.__calculate_current_coordinates(current_time, time1, time2,
                                                 stop_coordinates,
                                                 stop_durations)

        return current_coordinates

    def __calculate_current_coordinates(self, current_time, time1, time2,
                                        coordinates, durations_frac):

        current_duration = current_time - time1
        durations = [d * (time2 - time1) for d in durations_frac]
        cumulative_durations = np.cumsum(durations)

        current_i = 0
        for i in range(len(durations_frac)):
            if current_duration >= cumulative_durations[i]:
                current_i = i

        coordinates1 = coordinates[current_i + 1]
        if current_i + 2 < len(coordinates):
            coordinates2 = coordinates[current_i + 2]
            duration1 = cumulative_durations[current_i]
            duration2 = cumulative_durations[current_i + 1]

            current_coordinates = \
                self.__interpolate_coordinates(coordinates1, coordinates2,
                                               duration1, duration2,
                                               current_duration)
        else:
            # Vehicle is at the end of the route (i.e., coordinates1 is the
            # last coordinates)
            current_coordinates = coordinates1

        return current_coordinates

    def __interpolate_coordinates(self, coordinates1, coordinates2, time1,
                                  time2, current_time):
        inter_factor = (current_time - time1) / (time2 - time1)

        current_lon = inter_factor * (coordinates2[0]
                                      - coordinates1[0]) + coordinates1[0]
        current_lat = inter_factor * (coordinates2[1]
                                      - coordinates1[1]) + coordinates1[1]
        current_coordinates = (current_lon, current_lat)

        return current_coordinates

    def __extract_polylines_from_response(self, res, stop_ids):

        polylines = {}

        legs = res['routes'][0]['legs']
        coordinates = polyline.decode(res["routes"][0]["geometry"],
                                      geojson=True)

        if len(legs) != (len(stop_ids) - 1):
            logger.warning("len(legs) ({}) is different from  len(stop_ids) "
                           "({})".format(len(legs), len(stop_ids)))

        start_coord_index = 0
        for leg_index in range(len(legs)):
            leg = legs[leg_index]

            leg_durations = leg['annotation']['duration']
            total_duration = sum(leg_durations)
            leg_durations_frac = [d / total_duration for d in leg_durations] \
                if total_duration > 0 else [1]

            end_coord_index = start_coord_index + len(leg_durations) + 1
            leg_coordinates = coordinates[start_coord_index:end_coord_index]
            leg_polyline = polyline.encode(leg_coordinates, geojson=True)

            # polylines[stop_ids[leg_index]] = (leg_polyline, leg_durations_frac)
            polylines[str(leg_index)] = (leg_polyline, leg_durations_frac)

            # The last coordinates of a given leg are the same as the first
            # coordinates of the next leg
            start_coord_index = end_coord_index - 1

        return polylines


class CoordinatesOSRMOld(Coordinates):
    def __init__(self, config=None):
        super().__init__()

        config = CoordinatesOSRMConfig() if config is None else config
        self.__osrm_url = config.url
        self.__future_polylines_osrm = config.future_polylines_osrm

        self.__vehicle_positions_dict = {}
        self.__trip_positions_dict = {}

        self.__vehicle_past_polylines_dict = {}
        self.__vehicle_future_polylines_dict = {}
        self.__trip_past_polylines_dict = {}
        self.__trip_future_polylines_dict = {}
        self.__osrm_response_dict = {}
        self.__polylines_osrm_response_dict = {}
        self.__coordinates_segments_dict = {}

    def update_position(self, vehicle, route, current_time):

        current_position = get_from_time_dict(
            vehicle.id, current_time, self.__vehicle_positions_dict)

        if current_position is None and route is None:
            current_position = None
        elif current_position is None \
                and route.current_stop is not None:
            current_position = route.current_stop.location
        elif current_position is None \
                and len(route.previous_stops) > 0:
            # Current position is between two stops
            stop1 = route.previous_stops[-1]
            stop2 = route.next_stops[0]

            current_coordinates = self.__get_coordinates_from_osrm(
                current_time,
                stop1.departure_time,
                stop1.location.lon,
                stop1.location.lat,
                stop2.arrival_time,
                stop2.location.lon,
                stop2.location.lat)

            current_position = TimeCoordinatesLocation(current_time,
                                                       current_coordinates[0],
                                                       current_coordinates[1])

        update_time_dict(current_position, vehicle.id, current_time,
                         self.__vehicle_positions_dict)

        return current_position

    def update_trip_positions(self, trip, time, position):

        update_time_dict(position, trip.id, time, self.__trip_positions_dict)

        return position

    def update_vehicle_past_polyline(self, vehicle):

        past_polyline = None

        positions_by_time = self.__vehicle_positions_dict[vehicle.id]
        positions = []
        previous_coord = None
        for time, position in positions_by_time.items():
            current_coord = (position.lon, position.lat)
            if current_coord != previous_coord:
                positions.append(current_coord)
                previous_coord = current_coord

        if len(positions) > 1:
            past_polyline = polyline.encode(positions, geojson=True)

        return past_polyline

    def update_trip_past_polyline(self, trip):

        past_polyline = None

        if trip.id in self.__trip_positions_dict:
            positions_by_time = self.__trip_positions_dict[trip.id]
            positions = []
            previous_coord = None
            for time, position in positions_by_time.items():
                current_coord = (position.lon, position.lat)
                if current_coord != previous_coord:
                    positions.append(current_coord)
                    previous_coord = current_coord

            if len(positions) > 1:
                past_polyline = polyline.encode(positions, geojson=True)

        return past_polyline

    def update_vehicle_future_polyline(self, vehicle, current_time):

        future_polyline = get_from_time_dict(
            vehicle, current_time, self.__vehicle_future_polylines_dict)
        if future_polyline is None:
            future_polyline = self.__update_vehicle_future_polyline(vehicle)
            update_time_dict(future_polyline, vehicle.id, current_time,
                             self.__vehicle_future_polylines_dict)

        return future_polyline

    def update_trip_future_polyline(self, trip, current_time):

        future_polyline = get_from_time_dict(
            trip, current_time, self.__trip_future_polylines_dict)
        if future_polyline is None:
            future_polyline = self.__update_trip_future_polyline(trip)
            update_time_dict(future_polyline, trip.id, current_time,
                             self.__trip_future_polylines_dict)

        return future_polyline

    def __get_coordinates_from_osrm(self, current_time, time1, lon1, lat1,
                                    time2, lon2, lat2):

        service_url = "route/v1/driving/"
        args_url = "?annotations=true&overview=full"
        coord_url = "{},{};{},{}".format(lon1, lat1, lon2, lat2)

        if coord_url in self.__osrm_response_dict:
            response = self.__osrm_response_dict[coord_url]
        else:
            request_url = self.__osrm_url + service_url + coord_url + args_url
            response = requests.get(request_url)
            self.__osrm_response_dict[coord_url] = response

        route_res = response.json()
        coordinates = polyline.decode(route_res['routes'][0]['geometry'],
                                      geojson=True)
        durations = route_res['routes'][0]['legs'][0]['annotation']['duration']
        # We should always have that len(durations) == len(coordinates) - 1

        current_coordinates = \
            self.__calculate_current_coordinates(current_time, time1, time2,
                                                 coordinates, durations)

        return current_coordinates

    def __calculate_current_coordinates(self, current_time, time1, time2,
                                        coordinates, durations):
        current_time_factor = (current_time - time1) / (time2 - time1)
        cumulative_durations = np.cumsum(durations)
        total_duration = cumulative_durations[-1]
        current_duration = current_time_factor * total_duration

        current_i = 0
        for i in range(len(durations)):
            if current_duration >= cumulative_durations[i]:
                current_i = i

        coordinates1 = coordinates[current_i + 1]
        if current_i + 2 < len(coordinates):
            coordinates2 = coordinates[current_i + 2]
            duration1 = cumulative_durations[current_i]
            duration2 = cumulative_durations[current_i + 1]
            current_coordinates = \
                self.__interpolate_coordinates(coordinates1, coordinates2,
                                               duration1, duration2,
                                               current_duration)
        else:
            # Vehicle is at the end of the route (i.e., coordinates1 is the
            # last coordinates)
            current_coordinates = coordinates1

        return current_coordinates

    def __interpolate_coordinates(self, coordinates1, coordinates2, time1,
                                  time2, current_time):
        inter_factor = (current_time - time1) / (time2 - time1)

        current_lon = inter_factor * (coordinates2[0]
                                      - coordinates1[0]) + coordinates1[0]
        current_lat = inter_factor * (coordinates2[1]
                                      - coordinates1[1]) + coordinates1[1]
        current_coordinates = (current_lon, current_lat)

        return current_coordinates

    def __update_vehicle_future_polyline(self, vehicle):

        future_polyline = None
        future_coordinates = []

        if vehicle.position is not None:
            future_coordinates.append((vehicle.position.lon,
                                       vehicle.position.lat))

        for stop in vehicle.route.next_stops:
            stop_coord = (stop.location.lon, stop.location.lat)
            future_coordinates.append(stop_coord)

        if len(future_coordinates) > 1 and self.__future_polylines_osrm:
            future_polyline = \
                self.__get_polyline_from_osrm(future_coordinates)
        elif len(future_coordinates) > 1:
            future_polyline = polyline.encode(future_coordinates,
                                              geojson=True)

        return future_polyline

    def __update_trip_future_polyline(self, trip):

        future_polyline = None
        future_coordinates = []

        if trip.position is not None:
            future_coordinates.append((trip.position.lon, trip.position.lat))

        if trip.current_leg.assigned_vehicle is not None:
            current_leg_next_stops = get_next_stops_until_dest(
                trip.current_leg.destination,
                trip.current_leg.assigned_vehicle.route)
            for stop in current_leg_next_stops:
                stop_coord = (stop.location.lon, stop.location.lat)
                future_coordinates.append(stop_coord)

        if len(future_coordinates) > 1 and self.__future_polylines_osrm:
            future_polyline = \
                self.__get_polyline_from_osrm(future_coordinates)
        elif len(future_coordinates) > 1:
            future_polyline = polyline.encode(future_coordinates,
                                              geojson=True)

        return future_polyline

    def __get_polyline_from_osrm(self, coordinates_list):
        coordinates_str_list = [str(coord[0]) + "," + str(coord[1]) for coord
                                in coordinates_list]

        service_url = "route/v1/driving/"
        args_url = ""
        coord_url = ";".join(coordinates_str_list)

        if coord_url in self.__polylines_osrm_response_dict:
            response = self.__polylines_osrm_response_dict[coord_url]
        else:
            request_url = self.__osrm_url + service_url + coord_url + args_url
            response = requests.get(request_url)
            self.__polylines_osrm_response_dict[coord_url] = response

        route_res = response.json()

        if route_res['code'] == 'Ok':
            returned_polyline = route_res['routes'][0]['geometry']
        else:
            returned_polyline = None

        return returned_polyline


def get_from_time_dict(key, time, time_dict):
    value = None
    if key in time_dict and time \
            in time_dict[key]:
        value = time_dict[key][time]

    return value


def update_time_dict(value, key, time, time_dict):
    if key not in time_dict:
        time_dict[key] = {}
    time_dict[key][time] = value


def get_next_stops_until_dest(destination, route):
    stops_list = []

    destination_found = False

    if route.current_stop is not None:
        stops_list.append(route.current_stop)

        if route.current_stop.location == destination:
            destination_found = True

    if not destination_found:
        for stop in route.next_stops:
            stops_list.append(stop)
            if stop.location == destination:
                destination_found = True
                break

    if not destination_found:
        # Destination stop is in previous leg (may happen if
        # PassengerStatus is COMPLETE).
        stops_list = []

    return stops_list
