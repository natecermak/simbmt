import logging
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


class StaticRouteOracle:
    def __init__(self, params: Dict):
        self.params = params  # keep track of simulation parameters

    def set_grid_routes(self, nx: int, ny: int) -> None:
        self.routes = []
        for i in range(nx):
            self.routes.append(np.array([[0, i / (nx - 1)], [1, i / (nx - 1)]]))
        for i in range(ny):
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

    def pickup_and_dropoff(self, state, time) -> None:
        pass
