import logging

import numpy as np


logger = logging.getLogger(__name__)


def is_near(a, b, eps):
    return np.linalg.norm(a - b) <= eps


class NaberOracle:
    def __init__(self, params, state):
        self.params = params
        for bus in state.busses:
            bus.assignment = None

    def route(self, state):
        # if there's an unassigned passenger, and any available bus,
        #    assign the passenger to the bus
        assignments = [bus.assignment for bus in state.busses]

        for p in state.passengers:
            if p not in assignments and not p.on_bus:
                # assign it to an empty bus, if available
                for bus in state.busses:
                    if bus.assignment is None:
                        bus.assignment = p
                        logger.debug(f"Passenger {p.id} assigned to bus {bus.id}")
                        break

        # for every bus that has an assignment, go pick them up if they're not already aboard
        for bus in state.busses:
            if bus.assignment is not None:
                if bus.assignment not in bus.passengers:
                    # if we havent picked them up, got to them
                    dir = bus.assignment.loc - bus.loc
                else:
                    # if bus has an assignment as passenger, go to their destination
                    dir = bus.assignment.destination - bus.loc

                bus.vel = dir / np.linalg.norm(dir) * self.params["bus_speed"]

                # handle the last step to a target (don't overshoot)
                if np.linalg.norm(dir) < self.params["bus_speed"]:
                    bus.vel = dir

    def pickup_and_dropoff(self, state, time):
        for bus in state.busses:
            if bus.assignment is not None:
                if (
                    is_near(bus.loc, bus.assignment.loc, self.params["pickup_eps"])
                    and not bus.assignment.on_bus
                ):
                    bus.pickup(bus.assignment)
            for p in bus.passengers:
                if is_near(bus.loc, bus.assignment.destination, self.params["pickup_eps"]):
                    bus.dropoff(p, time)
                    bus.vel = np.zeros(2)
                    bus.assignment = None
