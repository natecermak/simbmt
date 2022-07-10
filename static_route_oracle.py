import logging
from typing import Dict

import numpy as np

import trigonometry as trig

logger = logging.getLogger(__name__)


class StaticRouteOracle:
    def __init__(self, params: Dict):
        self.params = params  # keep track of simulation parameters

    def set_grid_routes(self, nx: int, ny: int) -> None:
        self.routes = []
        for i in range(nx):
            if nx == 1:
                self.routes.append(np.array([[0, 0.5], [1, 0.5]]))
            else:
                self.routes.append(np.array([[0, i / (nx - 1)], [1, i / (nx - 1)]]))
        for i in range(ny):
            if ny == 1:
                self.routes.append(np.array([[0.5, 0], [0.5, 1]]))
            else:
                self.routes.append(np.array([[i / (ny - 1), 0], [i / (ny - 1), 1]]))

    def set_spoke_routes(self, ns: int) -> None:
        # TODO: define this
        pass

    def set_hub_and_spoke_routes(self, nh: int, ns: int) -> None:
        # TODO: define this
        pass

    def initialize_busses(self, state, num_routes: int) -> None:
        # evenly distribute busses between routes
        for i, bus in enumerate(state.busses):
            frac = i * num_routes / len(state.busses)
            bus.route = int(frac)
            route = self.routes[bus.route]

            # add `tci` (target coordinate index - the index of the route coordinates that is the current bus destination)
            phase = frac - bus.route
            nv = self.routes[bus.route].shape[0]  # number of vertices
            bus.tci = int(phase * nv)
            if bus.tci == nv:
                bus.tci = 0
                bus.loc = (route[-1] + route[0]) / 2
            else:
                bus.loc = (route[bus.tci] + route[bus.tci - 1]) / 2

    def route(self, state) -> None:
        for bus in state.busses:
            route = self.routes[bus.route]
            if np.all(bus.loc == route[bus.tci]):
                bus.tci = (bus.tci + 1) % len(route)

            dir = route[bus.tci] - bus.loc
            bus.vel = dir / np.linalg.norm(dir) * self.params["bus_speed"]

            # handle the last step to a target (don't overshoot)
            if np.linalg.norm(dir) < self.params["bus_speed"]:
                bus.vel = dir

        for passenger in state.passengers:
            if passenger.on_bus:
                continue  # irrelevant they're already on bus.

            # Do we come up with the plan as soon as they pop into existence and then save it?
            # Or do we continually re-derive it?
            # For now, do the former

            if not hasattr(passenger, "plan"):
                self.derive_plan(passenger, state)
            # TODO:
            # passenger.vel = derive_vel_from_plan(passenger)

    def pickup_and_dropoff(self, state, time) -> None:
        pass

    def derive_plan(self, passenger, state):
        # 1. check the walking time. that's a cheap upper bound.
        walking_time = (
            np.linalg.norm(passenger.destination - passenger.loc) / self.params["passenger_speed"]
        )

        # check which buses it is even possible to get on
        for bus in state.busses:
            timetable = self.get_bus_timetable(bus, 1)
            for row in timetable:

                ls = trig.get_accessible_region(
                    p=passenger.loc,
                    b1=row[1:3],
                    b2=row[3:5],
                    t1=row[0],
                    vp=self.params['passenger_speed'],
                    vb=self.params['bus_speed'],
                )
                if ls is None:
                    print(f"Unreachable: {row}")
                else:
                    print(f"Can reach:   {row}")
        # TODO: Placeholder for now
        passenger.plan = True


    def get_bus_timetable(self, bus, t_max):
        """ get a n x 5 table (t, x0, y0, x1, y1) from NOW (t=0) till t=t=max """
        table = np.empty((10, 5))
        route = self.routes[bus.route]
        print(route)
        print(len(route))
        table[0, 0] = 0
        table[0, 1:3] = bus.loc
        table[0, 3:5] = route[bus.tci]

        for i in range(1, 10):
            # time at which the bus starts this line segment
            table[i, 0] = table[i - 1, 0] + np.linalg.norm(table[i-1, 3:5] - table[i-1, 1:3]) / self.params['bus_speed']

            # start and end coordinates of this segment
            table[i, 1:3] = route[(bus.tci + i - 1) % len(route)]
            table[i, 3:5] = route[(bus.tci + i) % len(route)]

        # print(f"Bus {bus.id} on route {bus.route} has upcoming timetable:")
        # print(table)
        # input()

        return table
    